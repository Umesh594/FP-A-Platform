from pydantic import BaseModel, EmailStr, Field

class UserCreateSchema(BaseModel):
    email: EmailStr
    full_name: str
    password: str

    model_config = {
        "from_attributes": True
    }


class UserReadSchema(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    is_active: bool = Field(default=True)

    model_config = {
        "from_attributes": True
    }