from datetime import datetime
from pydantic import BaseModel, ConfigDict


class KycDocumentGrant(BaseModel):
    url: str
    expires_in: int


class KycDocumentsResponse(BaseModel):
    status: str
    masked_citizen_id: str
    front: KycDocumentGrant
    back: KycDocumentGrant
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)
