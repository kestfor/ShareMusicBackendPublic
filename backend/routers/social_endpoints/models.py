from pydantic import BaseModel


class RelationUpdateInfo(BaseModel):
    first_user_id: int
    second_user_id: int
    action: str

