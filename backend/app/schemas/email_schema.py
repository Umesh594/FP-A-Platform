from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional

class EmailSchema(BaseModel):
    subject: str
    content: str
    to_email: EmailStr
    attachments: Optional[List[str]] = Field(default_factory=list)

    model_config = {
        "from_attributes": True
    }