from advanced_alchemy.base import UUIDAuditBase
from sqlalchemy.orm import Mapped, mapped_column, relationship


class RoleModel(UUIDAuditBase):
    __tablename__ = "roles"

    name: Mapped[str] = mapped_column(unique=True)
    permissions = relationship(
        "PermissionModel",
        secondary="roles_permissions",
        lazy="selectin",
    )
