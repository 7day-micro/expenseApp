# Initial schemas

from pydantic import BaseModel
from typing import Optional


class CategorySchema(BaseModel):
    id: int
    name: str
    # TODO define color icon format -> color -> hex / icon -> url for svg/png?
    # TODO check if this table need the creaed_at and updated_at field as required at project_scope file, item #3
    color: Optional[str]
    icon: Optional[str]

    class Meta:
        from_attributes = True


class CategoryCreateSchema(BaseModel):
    name: str
    color: Optional[str]
    icon: Optional[str]
