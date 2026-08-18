from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from datetime import datetime, timedelta, timezone
from app.database.connection import Base
from app.models.admin_model import AdminUsers


IST = timezone(timedelta(hours=5, minutes=30))
class MasterColors(Base):
    __tablename__ = "tbl_master_colors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=True)
    description = Column(String(500), nullable=True)

    status = Column(Integer, default=1)
    createdBy = Column(Integer, ForeignKey("tbl_admin.id"),nullable=True)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedBy = Column(Integer, ForeignKey("tbl_admin.id"),nullable=True)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deletedBy = Column(Integer, nullable=True)
    deletedAt = Column(DateTime, nullable=True)


    created_by_user = relationship("AdminUsers",foreign_keys=[createdBy],lazy="selectin")
    updated_by_user = relationship("AdminUsers",foreign_keys=[updatedBy],lazy="selectin")


    # FORMATTED PROPERTIES (READ-ONLY)
    @property
    def createdAtFormatted(self):
        return (
            self.createdAt.astimezone(IST).strftime("%d-%b-%Y %H:%M:%S")
            if self.createdAt else None
        )
 
    @property
    def updatedAtFormatted(self):
        return (
            self.updatedAt.astimezone(IST).strftime("%d-%b-%Y %H:%M:%S")
            if self.updatedAt else None
        )
 