# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List

from pydantic import Field as FieldInfo

from ..._models import BaseModel

__all__ = ["CommunicationSendEmailResponse", "Attachment"]


class Attachment(BaseModel):
    id: str

    file_name: str = FieldInfo(alias="fileName")


class CommunicationSendEmailResponse(BaseModel):
    """
    Indicates the email request was accepted and processed (or queued for processing).
    """

    attachments: List[Attachment]
    """The attachments that were sent with the email.

    If zipAttachments was true, this will contain the single zipped file.
    """
