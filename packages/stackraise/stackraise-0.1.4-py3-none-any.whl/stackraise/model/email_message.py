from typing import Annotated, Optional
from unittest.mock import Base

from .core import Base, Field
from .dto import Dto
from .file import File
from .name_email import NameEmail
from .time_range import DateTime


class _EmailMessageBase(Base):
    subject: Annotated[
        Optional[str],
        Field(default=None),
    ]
    body: Annotated[
        str,
        Field(),
    ]
    date: Annotated[
        DateTime,
        Field(),
    ]
    sender: Annotated[
        NameEmail,
        Field(),
    ]
    to: Annotated[
        list[NameEmail],
        Field(default_factory=list),
    ]
    cc: Annotated[
        list[NameEmail],
        Field(default_factory=list),
    ]

class EmailMessage(_EmailMessageBase):


    attachment: Annotated[
        list[File.Ref],
        Field(default_factory=list),
    ]

    async def attachments(self):
        for attachment_ref in self.attachment:
            yield await attachment_ref.fetch()
        
    async def fetch_attachments(self):
        files = [await ref.fetch() for ref in self.attachment]
        return self.WithEmbeddedAttachments(
            subject=self.subject,
            body=self.body,
            date=self.date,
            sender=self.sender,
            to=self.to,
            cc=self.cc,
            attachments=files,
        )


    class WithEmbeddedAttachments(_EmailMessageBase, Dto):
        attachments: Annotated[
            list[File],
            Field(default_factory=list),
        ]

        async def commit_attachments(self):
            attachments: list[File.Ref] = []
            for attachment in self.attachments:
                file = await attachment.store()
                attachments.append(file.ref)

            return EmailMessage(
                subject=self.subject,
                body=self.body,
                date=self.date,
                sender=self.sender,
                to=self.to,
                cc=self.cc,
                attachment=attachments,
            )






