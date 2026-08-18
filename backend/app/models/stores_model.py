# app/models/store_model.py
from sqlalchemy import Column, Integer, String, Float, DateTime,ForeignKey
from sqlalchemy.orm import relationship

from datetime import datetime,timedelta, timezone
from app.database.connection import Base


IST = timezone(timedelta(hours=5, minutes=30))

class Stores(Base):
    __tablename__ = "tbl_stores"

    id = Column(Integer, primary_key=True, index=True)

    store_name = Column(String(255), nullable=False)
    address = Column(String(500))
    city = Column(String(100))
    state = Column(String(100))
    pincode = Column(String(20))

    phone = Column(String(20))
    email = Column(String(255))

    latitude = Column(Float)
    longitude = Column(Float)

    store_type = Column(String(20), nullable=False)

    website = Column(String(255))

    products_id = Column(String(255), nullable=True)

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
 