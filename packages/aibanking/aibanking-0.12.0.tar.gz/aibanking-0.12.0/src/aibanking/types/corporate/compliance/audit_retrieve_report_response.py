# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from datetime import datetime

from pydantic import Field as FieldInfo

from ...._models import BaseModel

__all__ = ["AuditRetrieveReportResponse"]


class AuditRetrieveReportResponse(BaseModel):
    generated_at: datetime = FieldInfo(alias="generatedAt")

    report_id: str = FieldInfo(alias="reportId")

    findings: Optional[List[str]] = None
