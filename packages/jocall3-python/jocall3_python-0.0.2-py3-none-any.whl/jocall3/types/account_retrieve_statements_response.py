# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["AccountRetrieveStatementsResponse", "DownloadURLs"]


class DownloadURLs(BaseModel):
    csv: Optional[str] = None

    pdf: Optional[str] = None


class AccountRetrieveStatementsResponse(BaseModel):
    account_id: str = FieldInfo(alias="accountId")

    download_urls: DownloadURLs = FieldInfo(alias="downloadUrls")

    period: str

    statement_id: str = FieldInfo(alias="statementId")
