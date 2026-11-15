from sqlalchemy import Float, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Slot(Base):
    __tablename__ = "slots"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    provider: Mapped[str] = mapped_column(String, index=True)
    start: Mapped[str] = mapped_column(String)  # echoed back exactly as sent
    end: Mapped[str] = mapped_column(String)
    starts_at: Mapped[float] = mapped_column(Float, index=True)  # epoch, for sorting/compare
