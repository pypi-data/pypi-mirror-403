# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from pydantic import Field as FieldInfo

from ...._models import BaseModel

__all__ = ["AuditRequestAuditResponse"]


class AuditRequestAuditResponse(BaseModel):
    audit_id: Optional[str] = FieldInfo(alias="auditId", default=None)
