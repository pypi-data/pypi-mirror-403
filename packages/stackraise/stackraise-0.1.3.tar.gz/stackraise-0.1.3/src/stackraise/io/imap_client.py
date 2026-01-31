from __future__ import annotations

from email.message import Message
import imaplib
import html
from asyncio import get_event_loop
from contextlib import asynccontextmanager
from dataclasses import dataclass
from email import policy
from email.parser import BytesParser
from email.utils import parsedate_to_datetime
from functools import wraps
from ssl import SSLContext
from typing import Optional, Sequence
from datetime import datetime, timezone

import stackraise.model as model
from aioimaplib import IMAP4_SSL as InnerImapSslClient
#from pydantic import BaseModel

# TODO: implementar utilizando aioimaplib


class ImapError(Exception): ...


def in_executor(fn):
    @wraps(fn)
    async def wrapper(*args, **kwargs):
        loop = get_event_loop()
        return await loop.run_in_executor(None, fn, *args, **kwargs)

    return wrapper


@dataclass
class InboxInfo:
    exists: int
    recent: int
    uidvalidity: int
    #uidvalidity: bool
    flags: list[str]


import re

_SELECT_PATTERNS = {
    "exists": re.compile(r"(\d+)\s+EXISTS", re.I),
    "recent": re.compile(r"(\d+)\s+RECENT", re.I),
    "uidvalidity": re.compile(r"UIDVALIDITY\s+(\d+)", re.I),
    "uidnext": re.compile(r"UIDNEXT\s+(\d+)", re.I),
    "highestmodseq": re.compile(r"HIGHESTMODSEQ\s+(\d+)", re.I),
    "flags_block": re.compile(r"FLAGS\s*\((.*?)\)", re.I),  # captura lo de dentro de (...)
}

_GMAIL_QUOTE_RX = re.compile(
    r"(?is)<blockquote[^>]*class=[\"']?gmail_quote[^>]*>.*?</blockquote>"
)

#Quizás esto solo sirva para el formato de GMAIL
_REPLY_SEP_RX = re.compile(r"""(?imx)
^On\s.+\swrote:\s*$|
^El\s+\w{3},.+\sescribi[oó]:\s*$|
^De:\s.*$|
^From:\s.*$|
^-----Original Message-----\s*$|
^_{2,}\s*Forwarded message\s*_{2,}\s*$
""")


class ImapClient:
    class Settings(model.Base):
        server: str
        timeout: int = 10
        username: str
        password: str

    def __init__(self, settings: Settings):
        self._settings = settings
        self._ssl_context = SSLContext()

    @asynccontextmanager
    async def session(self):
        session = self.Session(self)
        async with session:
            yield session

    class Session:
        def __init__(self, client: ImapClient):
            self._client = client
            self._inner = InnerImapSslClient(
                client._settings.server,
                ssl_context=client._ssl_context,
                timeout=10,
            )

        async def __aenter__(self):
            await self._inner.wait_hello_from_server()
            await self._inner.login(
                self._client._settings.username, self._client._settings.password
            )

        async def __aexit__(self, exc_type, exc_value, traceback):
            await self._inner.logout()

        @staticmethod
        def _parse_select_payload(payload: list[bytes]) -> dict:
            info = {
                "exists": 0,
                "recent": 0,
                "uidvalidity": 0,
                "uidnext": None,
                "highestmodseq": None,
                "flags": [],
            }
            for raw in payload or []:
                line = raw.decode(errors="ignore")

                # números
                for key in ("exists", "recent", "uidvalidity", "uidnext", "highestmodseq"):
                    m = _SELECT_PATTERNS[key].search(line)
                    if m:
                        info[key] = int(m.group(1))

                # flags
                mflags = _SELECT_PATTERNS["flags_block"].search(line)
                if mflags:
                    # separa por espacios sin romper backslashes
                    flags_text = mflags.group(1).strip()
                    # ejemplo: "\Answered \Flagged \Draft \Deleted \Seen $NotPhishing $Phishing"
                    if flags_text:
                        info["flags"] = flags_text.split()

            return info
        
        @staticmethod
        def _extract_rfc822_bytes(payload):
            """
            Find the RFC822 message bytes in a FETCH payload.
            Handles common shapes returned by imaplib/aioimaplib:
            - [ (b'1 (RFC822 {n}', b'...raw...'), b')' ]
            - [ b'1 (RFC822 {n}', b'...raw...', b')' ]
            - dict-like with a bytes value
            """
            # list/tuple payload
            if isinstance(payload, (list, tuple)):
                for part in payload:
                    # tuple: (meta, bytes)
                    if isinstance(part, tuple) and len(part) >= 2 and isinstance(part[1], (bytes, bytearray)):
                        return bytes(part[1])
                    # raw bytes as a separate entry
                    if isinstance(part, (bytes, bytearray)):
                        # heuristics: looks like a full message if it has headers/body separator
                        if b"\r\n\r\n" in part or part.startswith(b"From:") or part.startswith(b"Received:"):
                            return bytes(part)

            # dict payload (some clients)
            if isinstance(payload, dict):
                for _, val in payload.items():
                    if isinstance(val, (bytes, bytearray)):
                        return bytes(val)

            # nothing found
            raise ImapError("Cannot find RFC822 bytes in FETCH payload")

        @staticmethod
        def _html_to_text(segment: str) -> str:
            """Helper function to convert HTML to plain text."""
            if not segment:
                return ""
            # quita quoted reply de Gmail
            segment = _GMAIL_QUOTE_RX.sub("", segment)
            # saltos de línea básicos
            segment = re.sub(r"(?i)<br\s*/?>", "\n", segment)
            segment = re.sub(r"(?i)</p\s*>", "\n\n", segment)
            # elimina el resto de etiquetas
            segment = re.sub(r"<[^>]+>", "", segment)
            # desescapa entidades (&quot; → ", &aacute; → á, etc.)
            segment = html.unescape(segment)
            # normaliza espacios
            segment = re.sub(r"[ \t]+", " ", segment)
            segment = re.sub(r"\n{3,}", "\n\n", segment).strip()
            return segment


        @staticmethod
        def _pick_body_part(msg: Message, prefer: Sequence[str] = ("plain", "html")) -> Message:
            """
            Returns a Message that is text/plain or text/html according to preference.
            If there's no multipart, returns msg.
            """
            # Nuevo API con policy.default
            part = msg.get_body(preferencelist=list(prefer))
            if part:
                return part
            # fallback: busca a mano
            if msg.is_multipart():
                for p in msg.walk():
                    ctype = (p.get_content_maintype(), p.get_content_subtype())
                    if ctype == ("text", "plain"):
                        return p
                for p in msg.walk():
                    ctype = (p.get_content_maintype(), p.get_content_subtype())
                    if ctype == ("text", "html"):
                        return p
            return msg


        @staticmethod
        def _strip_quoted_plaintext(s: str) -> str:
            """
            Removes quoted text from replies/forwards in plain text:
            - Cuts from known separators (Gmail/Outlook)
            - Discards quoted lines that start with '>'
            """
            if not s:
                return ""
            lines = s.splitlines()
            out = []
            for line in lines:
                # if we find a thread separator, cut there
                if _REPLY_SEP_RX.match(line):
                    break
                # ignore quote lines like "> ..."
                if line.strip().startswith(">"):
                    continue
                out.append(line)
            text = "\n".join(out).strip()
            # collapse excessive line breaks
            text = re.sub(r"\n{3,}", "\n\n", text)
            return text


        async def select(self, mailbox: str):
            status, payload = await self._inner.select(mailbox)
            if status != "OK":
                txt = ", ".join(e.decode() for e in (payload or []))
                raise ImapError(f"IMAPError '{status}' selecting mailbox '{mailbox}': {txt}")

            info = self._parse_select_payload(payload)

            # log opcional
            print(
                f"Mailbox selected successfully: EXISTS={info['exists']} RECENT={info['recent']} "
                f"UIDVALIDITY={info['uidvalidity']} FLAGS={info['flags']}"
            )

            return InboxInfo(
                exists=info["exists"],
                recent=info["recent"],
                uidvalidity=info["uidvalidity"],
                flags=info["flags"],
            )


        async def search(self, *criteria):
            # match await self._inner.search(None, *criteria):
            #     case "OK", messages:
            #         return messages[0].split() if messages[0] else []
            #     case err, payload:
            #         payload = ", ".join(e.decode() for e in payload)
            #         raise ImapError(
            #             f"IMAPError '{err}' searching emails with criteria {criteria}: {payload}"
            #         )
            def _tokenize(x):
                if isinstance(x, (list, tuple)):
                    for y in x:
                        yield from _tokenize(y)
                elif isinstance(x, str):
                    for t in x.split():
                        yield t
                else:
                    yield str(x)

            final_args = list(_tokenize(criteria))  # SIN charset None
            status, messages = await self._inner.search(*final_args)

            if status == "OK":
                ids = messages[0].split() if messages and messages[0] else []
                # devuelve siempre str
                return [i.decode() if isinstance(i, (bytes, bytearray)) else str(i) for i in ids]
            else:
                payload = ", ".join(e.decode() for e in (messages or []))
                raise ImapError(
                    f"IMAPError '{status}' searching emails with criteria {criteria}: {payload}"
                )

            
        async def tag(self, email_id, command: str, flags: str):
            match await self._inner.store(email_id, "+X-GM-LABELS", flags):
                case "OK", payload:
                    pass
                case err, payload:
                    payload = ", ".join(e.decode() for e in payload)
                    raise ImapError(
                        f"IMAPError '{err}' tagging email '{email_id}' with '{command} {flags}': {payload}"
                    )


        async def fetch(
            self,
            email_id: str,
            body_content_type_preference: Sequence[str] = ("plain", "html"),
        )   -> model.EmailMessage.WithEmbeddedAttachments:
            """
            Fetches an email by its ID and returns its content and attachments.
            Args:
                email_id (str): The ID of the email to fetch.
                body_content_type_preference (Sequence[str]): A sequence of content types to prefer when extracting
                    the body of the email. The first matching content type will be used.
            Returns:
                model.EmailMessage.WithEmbeddedAttachments: An object containing the email's metadata, body, and attachments.

            Note:
                This method uses the IMAP FETCH command to retrieve the email content and attachments.
                Attachments are parsed from the email content and returned as a list of File objects separately,
                so they can be stored or processed independently.
            """
            status, payload = await self._inner.fetch(str(email_id), "(RFC822)")
            if status != "OK":
                payload_text = ", ".join(
                    (p.decode() if isinstance(p, (bytes, bytearray)) else str(p)) for p in (payload or [])
                )
                raise ImapError(f"IMAPError '{status}' fetching email '{email_id}': {payload_text}")

            # Extract raw RFC822 bytes safely
            raw_bytes = self._extract_rfc822_bytes(payload)
            if not isinstance(raw_bytes, (bytes, bytearray)):
                raise ImapError(f"FETCH returned no RFC822 bytes for {email_id}; got {type(raw_bytes)}: {repr(raw_bytes)[:200]}")

            email_content = BytesParser(policy=policy.default).parsebytes(raw_bytes)

            attachments = []

            for part in email_content.walk():
                if part.get_content_maintype() == "multipart":
                    continue
                if part.get("Content-Disposition") is None:
                    continue
                if (filename := part.get_filename()) is not None:
                    attachments.append(
                        model.File.new(
                            filename=filename,
                            content_type=part.get_content_type(),
                            content=part.get_payload(decode=True),
                            disposition=part.get("Content-Disposition"),
                        )
                    )

            body_part = self._pick_body_part(email_content, prefer=body_content_type_preference)
            raw_body = body_part.get_content()

            if body_part.get_content_type() == "text/html":
                body_text = self._html_to_text(raw_body)
                body_text = self._strip_quoted_plaintext(body_text)
            else:
                body_text = self._strip_quoted_plaintext(raw_body)

            date_header = email_content.get("date")
            dt = parsedate_to_datetime(date_header) if date_header else datetime.now(timezone.utc)

            return model.EmailMessage.WithEmbeddedAttachments(
                    date=dt,
                    sender=model.NameEmail.from_str(email_content.get("from").strip()),
                    to=_parse_name_email_list(email_content.get("to", "")),
                    cc=_parse_name_email_list(email_content.get("cc", "")),
                    subject=email_content.get("subject"),
                    # body=email_content.get_body(
                    #     body_content_type_preference
                    # ).get_payload(),
                    body=body_text,
                    attachments=attachments,
                )




def _parse_name_email_list(s: str):
    return [model.NameEmail.from_str(e.strip()) for e in s.split(",")] if s else []


if __name__ == "__main__":


    async def main():

        imap = ImapClient(
            ImapClient.Settings(
                server="imap.gmail.com",
                username="proyectoleitat@gmail.com",
                password="fjej yfzg xgon pohk",
            )
        )

        async with imap.session():
            inbox = await imap.select("INBOX")
            print(inbox)
            email_ids = await imap.search('NOT X-GM-LABELS "PROCESSED"')
            print("EMAIL IDS", email_ids)
            email = await imap.fetch(email_ids[0])
