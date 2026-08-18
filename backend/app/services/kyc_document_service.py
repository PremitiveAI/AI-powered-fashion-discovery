
from fastapi import UploadFile, Request 
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse 
from pathlib import Path
from rapidfuzz import fuzz
import json, re, math

from app.utils.kyc_document_parser import (ocr_extract_text, extract_details, gen_embedding, parse_search_query, parse_date, build_answer)
from app.repositories.document_repository import DocumentRepository
from app.utils.response import success_response, error_response
from app.utils.crypto import encrypt_id, decrypt_id
from app.vector.vector_db import vector_db
from app.services.employee_service import EmployeeService

from app.models.pan_model import PAN
from app.models.aadhaar_model import Aadhaar
from app.models.resume_model import Resume
from app.models.address_proof_model import AddressProof
from app.models.qualification_model import Qualification


# ============================================================
# FILE UTILITIES
# ============================================================
def secure_filename(name: str):
    return re.sub(r"[^A-Za-z0-9._-]", "_", Path(name).name)

def save_local_file(user_id: str, employee_id: str , file: UploadFile):
    folder = Path(f"storage/{user_id}/{employee_id}")
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / secure_filename(file.filename)
    with open(path, "wb") as f:
        f.write(file.file.read())
    return str(path).replace("\\", "/")

def chunk_text(text: str, size=50_000):
    return [text[i:i + size] for i in range(0, len(text), size)]

def normalize(s):
    return " ".join(str(s or "").lower().split())

def is_valid_embedding(vec):
    return (
        isinstance(vec, list)
        and len(vec) > 100
        and all(isinstance(x, (int, float)) and not math.isnan(x) for x in vec)
    )

def _last_company(details: dict):
    history = details.get("work_history") or []
    return history[0].get("company") if history else None

def _skills(details: dict):
    skills = details.get("technical_skills") or []
    return ", ".join(skills)


# ============================================================
# UPSERT + VECTOR UPDATE
# ============================================================

def save_document_and_get_id(db: Session, emp_id: str, details: dict):
    doc_type = details.get("document_type")

    # Map doc_type → (Model, field mapping)
    field_map = {
        "pan_card": (PAN, {
            "pan_number": "doc_number",
            "full_name": "name",
            "date_of_birth": ("dob", parse_date),
            "father_name": ("extra.father_name", None),
        }),
        "aadhaar_card": (Aadhaar, {
            "aadhaar_number": "doc_number",
            "full_name": "name",
            "date_of_birth_or_yob": ("dob", parse_date),
            "gender": "gender",
            "address": "address",
        }),
        "resume": (Resume, {
            "full_name": "name",
            "email": "email",
            "mobile_number": "mobile",
            "total_experience_years": "work_experience_years",
            "last_company": ("details", _last_company),
            "skills": ("details", _skills),
        }),
        "address_proof": (AddressProof, {
            "full_name": "name",
            "address": "address",
            "document_name": "address_proof_type",
            "issue_date": ("extra.issue_date", parse_date),
        }),
        "qualification": (Qualification, {
            "full_name": "name",
            "highest_qualification": "highest_qualification",
            "institute_name": "institute_name",
            "specialization": "specialization",
            "year_of_passing": "year_of_passing",
        }),

    }

    if doc_type not in field_map:
        return None

    Model, mapping = field_map[doc_type]
    obj = db.query(Model).filter(Model.emp_id == emp_id, Model.deletedAt == None).first()

    # Build field values
    values = {"status": 1, "file_path": details.get("file_path")}
    for field, src in mapping.items():
        if isinstance(src, tuple):
            key, func = src
            val = details
            for part in key.split("."):
                val = val.get(part, {}) if isinstance(val, dict) else val
            values[field] = func(val) if func else val
        else:
            values[field] = details.get(src)

    if obj:
        for k, v in values.items():
            setattr(obj, k, v)
    else:
        obj = Model(emp_id=emp_id, **values)
        db.add(obj)

    db.commit()
    db.refresh(obj)
    return obj.id


def build_vector_payload(userId: str, employee_id:str, record_id: int, details: dict):
    dt = details["document_type"]

    if dt == "aadhaar_card":
        return (
            {   
                "document_id":f"{dt}_{record_id}",
                "userId": userId.lower(),
                "employeeId": employee_id,
                "document_type": dt.lower(),
                "full_name": details["name"].lower(),
                "record_id": record_id,
                "aadhaar_id": record_id,
                "aadhaar_number": details["doc_number"].lower(),
                "gender": details["gender"].lower(),
                "dob": details["dob"],
            },
            {
                "aadhaar_id": record_id,
                "full_name": details["name"],
                "aadhaar_number": details["doc_number"],
                "dob": details["dob"],
                "gender": details["gender"],
                "address": details["address"],
            }
        )

    if dt == "pan_card":
        return (
            {   
                "document_id":f"{dt}_{record_id}",
                "userId": userId.lower(),
                "employeeId": employee_id,
                "document_type": dt.lower(),
                "full_name": details["name"].lower(),
                "record_id": record_id,
                "pan_id": record_id,
                "pan_number": details["doc_number"].lower(),
            },
            {
                "pan_id": record_id,
                "full_name": details["name"],
                "pan_number": details["doc_number"],
                "dob": details["dob"],
                "father_name": details.get("extra", {}).get("father_name"),
            }
        )

    if dt == "resume":
        return (
            {   
                "document_id":f"{dt}_{record_id}",
                "userId": userId.lower(),
                "employeeId": employee_id,
                "document_type": dt.lower(),
                "full_name": details["name"].lower(),
                "record_id": record_id,
                "resume_id": record_id,
                "full_name": details["name"],
            },
            {
                "resume_id": record_id,
                "full_name": details["name"],
                "email": details["email"],
                "mobile": details["mobile"],
                "experience_years": details["work_experience_years"],
                "skills": details.get("technical_skills", []),
                "education": details.get("education_details", []),
                "work_history": details.get("work_history", []),
            }
        )

    if dt == "address_proof":
        return (
            {   
                "document_id":f"{dt}_{record_id}",
                "userId": userId.lower(),
                "employeeId": employee_id,
                "document_type": dt.lower(),
                "full_name": details["name"].lower(),
                "address_proof_type": details["address_proof_type"].lower(),
                "record_id": record_id,
                "address_proof_id": record_id,
                "full_name": details["name"].lower(),
            },
            {
                "address_proof_id": record_id,
                "address_proof_type": details["address_proof_type"],
                "full_name": details["name"],
                "email": details["email"],
                "mobile": details["mobile"],                
                "address": details["address"],               
            }
        )

    if dt == "qualification":
        return (
            {   
                "document_id":f"{dt}_{record_id}",
                "userId": userId.lower(),
                "employeeId": employee_id,
                "document_type": dt.lower(),
                "full_name": details["name"].lower(),
                "record_id": record_id,
                "qualification_id": record_id,
                "full_name": details["name"].lower(),
            },
            {
                "qualification_id": record_id,
                "full_name": details["name"],
                "highest_qualification": details["highest_qualification"],
                "institute_name": details["institute_name"],
                "specialization": details["specialization"],
                "year_of_passing": details["year_of_passing"],                              
            }
        )


    return {}, {}

def _process_single_file(db: Session, userId: str, employee_id:str, file: UploadFile):
    saved_path = save_local_file(userId, employee_id, file)    
    # text = ocr_extract_text(saved_path) # OCR + Extraction
    # details = extract_details(text)
    details["file_path"] = saved_path.replace("\\", "/")

    record_id = save_document_and_get_id(db, employee_id, details) # Save to correct table
    metadata, document_details = build_vector_payload(userId=userId, employee_id=employee_id,record_id=record_id, details=details) # Build vector payload

    # vector_db.delete_by_filter({})

    print("metadata.get('document_type') -------------------------->", metadata.get('document_type'))
    vector_db.delete_by_filter({
        "document_type": metadata.get('document_type'),
        "record_id": record_id
    })

    # Vector DB storage
    stored_chunks = 0
    for idx, chunk in enumerate(chunk_text(text)):
        if not chunk.strip():
            continue

        vector_db.add_vector(
            vector=gen_embedding(chunk),
            metadata={**metadata, "chunk": idx},
            document_details=document_details
        )
        stored_chunks += 1

    # API response
    return {
        "document_type": details["document_type"],
        "record_id": record_id,
        "name": details.get("name"),
        "doc_number": details.get("doc_number"),
        "file_path": saved_path,
        "chunks": stored_chunks,
    }


# ============================================================
# MULTI FILE UPLOAD
# ============================================================
def handle_upload_documents(db: Session, request:Request , userId: str, employee_id: str, files: list[UploadFile]):
    if not files:
        return error_response("No files uploaded", code=4000)
    employee_id = decrypt_id(employee_id)


    results, failed = [], []

    for file in files:
        try:
            result = _process_single_file(db, userId, employee_id, file)
            results.append(result)
        except Exception as e:
            failed.append({
                "filename": file.filename,
                "error": str(e)
            })

    return EmployeeService.get_employee_details(db, request, employee_id)
    # return success_response(
    #     "Files uploaded successfully",
    #     {
    #         "userId": userId,
    #         "uploaded": len(results),
    #         "failed": len(failed),
    #         "results": results,
    #         "errors": failed
    #     }
    # )












# ============================================================
# GLOBAL SEARCH (VECTOR FIRST)
# ============================================================

def handle_search_documents(db: Session, request: Request, query: str):
    user_id = request.state.userId
    parsed = parse_search_query(query)
    target_name = normalize(parsed.get("name"))
    query_vec = gen_embedding(query)

    where = {"userId": user_id.lower() }
    if parsed.get("document_type"):
        where["document_type"] = parsed["document_type"]

    if parsed.get("aadhaar_number"):
        where["aadhaar_number"] = parsed["aadhaar_number"]

    if parsed.get("pan_number"):
        where["pan_number"] = parsed["pan_number"]

    if target_name:
        where["full_name"] = target_name.lower()


    print("where =======================> ", where)

    hits = vector_db.search(query_vector=query_vec, top_k=50, where=where)

    grouped = {}

    for i in range(len(hits.get("ids", []))):

        meta = hits["metadatas"][i]
        raw = hits["documents"][i]
        dist = hits["distances"][i]

        if "record_id" not in meta or "document_type" not in meta:
            continue

        doc_type = meta["document_type"]
        record_id = meta["record_id"]

        payload = json.loads(raw) if isinstance(raw, str) else {}

        key = f"{doc_type}_{record_id}"

        score = (1 / (1 + dist)) + (
            fuzz.partial_ratio(target_name, normalize(payload.get("full_name"))) / 100
            if target_name else 0
        )

        if key not in grouped or grouped[key]["score"] < score:
            grouped[key] = {
                **payload,
                "document_type": meta["document_type"],
                "record_id": meta["record_id"],
                "score": round(score, 4)
            }
    results = list(grouped.values())
    answer = build_answer(query, results)



    # return success_response("Search results", {
    #     "query": query,
    #     "answer": answer,
    #     "results": results
    # })


# def build_answer(query: str, results: list) -> str:
#     if not results:
#         return "No matching information was found."

#     qtype = detect_question_type(query)

#     # ================= EXPERIENCE =================
#     if qtype == "experience_years":
#         resumes = [
#             r for r in results
#             if r.get("document_type") == "resume"
#             and r.get("experience_years") is not None
#         ]

#         if resumes:
#             r = resumes[0]
#             years = r["experience_years"]
#             name = r.get("full_name", "The candidate")
#             return f"{name} has {years} years of professional experience."

#         return "Experience information is not available."

#     # ================= PAN =================
#     if qtype == "pan_number":
#         for r in results:
#             if r.get("pan_number"):
#                 return f"The PAN number of {r.get('full_name')} is {r.get('pan_number')}."

#     # ================= AADHAAR =================
#     if qtype == "aadhaar_number":
#         for r in results:
#             if r.get("aadhaar_number"):
#                 return f"The Aadhaar number of {r.get('full_name')} is {r.get('aadhaar_number')}."

#     # ================= DOB =================
#     if qtype == "dob":
#         for r in results:
#             if r.get("dob"):
#                 return f"The date of birth of {r.get('full_name')} is {r.get('dob')}."

#     # ================= FALLBACK =================
#     return f"Found {len(results)} relevant document(s) for your query."


# def detect_question_type(query: str) -> str:
#     q = query.lower()

#     if "experience" in q or "years" in q:
#         return "experience_years"

#     if "pan number" in q:
#         return "pan_number"

#     if "aadhaar number" in q:
#         return "aadhaar_number"

#     if "dob" in q or "date of birth" in q:
#         return "dob"

#     if "address" in q:
#         return "address"

#     if "email" in q:
#         return "email"

#     if "mobile" in q or "phone" in q:
#         return "mobile"

#     return ""



# ============================================================
# DELETE DOCUMENT
# ============================================================

def handle_delete_document(db: Session, documentId: int):
    result = DocumentRepository(db).delete_document(documentId)
    if not result:
        return error_response("Document not found", code=4001)

    vector_db.delete_by_document(documentId)
    return success_response("Document deleted successfully")
