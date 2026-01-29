from advanced_alchemy.base import UUIDAuditBase
from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column


class AuthCodeModel(UUIDAuditBase):
    __tablename__ = "auth_codes"

    code: Mapped[str]
    action: Mapped[str]
    user_id = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))

    __table_args__ = (UniqueConstraint("user_id", "action", name="unique_user_action"),)
