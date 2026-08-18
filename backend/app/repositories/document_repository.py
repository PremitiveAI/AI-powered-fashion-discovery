# app/repositories/document_repository.py
from sqlalchemy.orm import Session
from app.models.documents_model import Documents as DocumentModel
from app.models.document_vectors_model import DocumentVectors
from typing import Optional

from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime, func
from pathlib import Path
import os

class DocumentRepository:
    def __init__(self, db: Session):
        self.db = db


    def create(self, **kwargs):
        doc = DocumentModel(**kwargs)
        self.db.add(doc)
        self.db.commit()
        self.db.refresh(doc)
        return doc

    def get_by_id(self, doc_id: int) -> Optional[DocumentModel]:
        return self.db.query(DocumentModel).filter(DocumentModel.id == doc_id).first()
    

    def delete(self, doc_id):
        doc = self.db.query(DocumentModel).filter(DocumentModel.id == doc_id).first()
        if doc:
            self.db.delete(doc)
            self.db.commit()

    def update_type(self, doc_id, new_type):
        doc = self.db.query(DocumentModel).filter(DocumentModel.id == doc_id).first()
        if doc:
            doc.document_type = new_type
            self.db.commit()
            return doc
        return None




    def get(self, documentId: int):
        return self.db.query(DocumentModel).filter(
            DocumentModel.id == documentId,
            DocumentModel.deletedAt == None
        ).first()

    def delete_document(self, documentId: int):
        """
        Fully delete:
        - Document record
        - File from storage
        - Vector entries
        """

        doc = self.get(documentId)
        if not doc:
            return None

        # 1. Delete file from storage
        try:
            file_path = Path(doc.file_path)
            if file_path.exists():
                file_path.unlink()
        except Exception as e:
            print("File delete error:", e)

        # 2. Delete all vectors for this document
        self.db.query(DocumentVectors).filter(
            DocumentVectors.documentId == documentId
        ).delete()

        # 3. Soft delete or hard delete?
        #    You have deletedAt so we soft delete
        doc.deletedAt = func.now()
        doc.deletedBy = 0     # set actual admin/user id

        self.db.commit()

        return True
