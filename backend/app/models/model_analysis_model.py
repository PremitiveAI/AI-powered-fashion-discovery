from sqlalchemy import Column, Integer, String, Text, DateTime, func
from app.database.connection import Base


class ModelAnalysisTable(Base):
    __tablename__ = "tbl_model_analysis"

    id = Column(Integer, primary_key=True, index=True)

    model_name = Column(String(255), nullable=True)
    model_url = Column(Text, nullable=False)
    user_url = Column(Text, nullable=True)

    prompt = Column(Text, nullable=True)

    status = Column(Integer, nullable=False, default=1)

    createdAt = Column(DateTime, server_default=func.now())
    updatedAt = Column(DateTime, server_default=func.now(), onupdate=func.now())
