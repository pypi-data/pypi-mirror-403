import asyncio
from email.message import EmailMessage
from logging import getLogger as get_logger
from smtplib import SMTP_SSL, SMTPException

import stackraise.di as di
import stackraise.model as model
from aiosmtplib import send

log = get_logger(__name__)

class SMTPClient(di.Singleton):
    """SMTP client for sending emails using SMTP over SSL."""
    class Settings(model.Base):
        server: str
        username: str
        password: str

    def __init__(self, settings: Settings):
        self.settings = settings

        self._inner: SMTP_SSL = None
        self._context_counter = 0

    async def connect(self):
        try:
            assert self._inner == None, f"SMTP client already connected"
            smpt_client = SMTP_SSL(self.settings.server)
            smpt_client.login(self.settings.username, self.settings.password)
            self._inner = smpt_client
        except SMTPException as e:
            log.info(f"Failed to connect to SMTP server: {e}")

    async def disconnect(self):
        if self._inner:
            self._inner.quit()
            self._inner = None

    async def __aenter__(self):
        self._context_counter += 1
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        self._context_counter -= 1
        if self._context_counter == 0:
            await self.disconnect()
        if exc_type:
            log.error(f"Error during SMTP operation: {exc_value}")

    async def send_email(self, email: model.EmailMessage | model.EmailMessage.WithEmbeddedAttachments):

        if not isinstance(email, model.EmailMessage.WithEmbeddedAttachments):
            email = await email.fetch_attachments()


        sender = str(email.sender if email.sender is not None else self.settings.username)

        to = [str(r) for r in email.to]

        # Create a standard RFC email message
        msg = EmailMessage()
        msg["From"] = sender
        msg["To"] = ", ".join(to)
        msg["Subject"] = email.subject
        msg.set_content(email.body)
        

        for attachment in email.attachments:
            content = await attachment.content()
            content_type = attachment.content_type or "application/octet-stream"
            maintype, subtype = content_type.split('/')
            msg.add_attachment(
                content,
                maintype=maintype,
                subtype=subtype,
                filename=attachment.filename
            )

        await send(msg, hostname=self.settings.server, 
                   #port=465,  # Default port for SMTP over SSL
                   username=self.settings.username,
                   password=self.settings.password,
                   use_tls=True
            )

        # loop = asyncio.get_running_loop()
        # await loop.run_in_executor(
        #     None,  # None = default thread pool
        #     lambda: self._inner.sendmail(sender, to, msg.as_string())
        # )




        # try:
        #     if not self._inner:
        #         log.info("Connection not established. Call connect() first.")
        #         return
            
        # except SMTPException as e:
        #     log.info(f"Failed to send email: {e}")
