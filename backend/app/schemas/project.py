from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from app.models.project import MemberRole
from app.schemas.user import UserOut


class ProjectBase(BaseModel):
    name: str
    key: str
    description: Optional[str] = None


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class ProjectMemberOut(BaseModel):
    id: int
    user: UserOut
    role: MemberRole
    joined_at: datetime

    class Config:
        from_attributes = True


class ProjectOut(ProjectBase):
    id: int
    owner_id: int
    owner: UserOut
    created_at: datetime
    members: List[ProjectMemberOut] = []

    class Config:
        from_attributes = True


class AddMemberRequest(BaseModel):
    email: str
    role: MemberRole = MemberRole.member


class UpdateRoleRequest(BaseModel):
    role: MemberRole
