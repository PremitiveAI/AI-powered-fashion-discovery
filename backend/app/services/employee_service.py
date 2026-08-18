from re import search
from sqlalchemy import or_, asc, desc
from sqlalchemy.orm import Session
from datetime import timezone, timedelta

from fastapi import APIRouter, Request, Response, Depends, UploadFile, File

from app.models.employee_model import Employee
from app.models.aadhaar_model import Aadhaar
from app.models.pan_model import PAN
from app.models.qualification_model import Qualification
from app.models.resume_model import Resume
from app.models.address_proof_model import AddressProof
from app.utils.crypto import encrypt_id,decrypt_id, mask_aadhaar, mask_pan


from app.utils.response import success_response, error_response

IST = timezone(timedelta(hours=5, minutes=30))
class EmployeeService:

    @staticmethod
    def _format_datetime(dt):
        return dt.astimezone(IST).strftime("%d-%b-%Y %H:%M:%S") if dt else None  

    @staticmethod
    def _response(emp: Employee):
        return {
            # "id": emp.id,
            "id": encrypt_id(emp.id),
            "emp_id": emp.emp_id,
            "emp_name": emp.emp_name,
            "status": emp.status,
            "createdAt": EmployeeService._format_datetime(emp.createdAt),
            "updatedAt": EmployeeService._format_datetime(emp.updatedAt),
        }

    # ------------------ Create / Update Employee ------------------
    @staticmethod
    def create_employee(db: Session, payload: dict):
        
        emp_pk = payload.get("id")   # ENCRYPTED PRIMARY KEY

        if emp_pk:
            try:
                emp_pk = decrypt_id(emp_pk)
            except Exception:
                return error_response("Invalid encrypted id", 400)

        name = payload.get("emp_name", "").strip()

        if not name:
            return error_response("Employee name is required")

        emp_id = payload.get("emp_id")
        emp_id = emp_id.strip() if emp_id else None

        # -------------------------------------------------
        # CHECK EMPLOYEE BY ID
        # -------------------------------------------------
        employee_by_id = None
        if emp_pk:
            employee_by_id = (
                db.query(Employee)
                .filter(Employee.id == emp_pk, Employee.status == 1)
                .first()
            )

        # -------------------------------------------------
        # UPDATE Employee
        # -------------------------------------------------
        if employee_by_id:

            # emp_name should NOT change
            # only emp_id update allowed

            if emp_id and employee_by_id.emp_id != emp_id:

                # check emp_id is not used by another employee
                emp_id_exists = (
                    db.query(Employee)
                    .filter(
                        Employee.emp_id == emp_id,
                        Employee.id != employee_by_id.id,
                        Employee.status == 1
                    )
                    .first()
                )

                if emp_id_exists:
                    return error_response("Employee ID already exists with a different employee",4090)

                employee_by_id.emp_id = emp_id
                db.commit()
                db.refresh(employee_by_id)

                return success_response("Employee ID updated successfully",EmployeeService._response(employee_by_id))

            return success_response("Employee already exists",EmployeeService._response(employee_by_id))

        # -------------------------------------------------
        # CREATE NEW EMPLOYEE
        # -------------------------------------------------
        if not emp_id:
            emp_id = Employee.generate_emp_id()

        emp_id_exists = (
            db.query(Employee)
            .filter(Employee.emp_id == emp_id, Employee.status == 1)
            .first()
        )

        if emp_id_exists:
            return error_response("Employee ID already exists with a different employee",4090)

        emp = Employee(
            emp_name=name,
            emp_id=emp_id
        )

        db.add(emp)
        db.commit()
        db.refresh(emp)

        return success_response("Employee created successfully",EmployeeService._response(emp))
    
    # --------Get Emp Details----------------------

    @staticmethod
    def get_employee_details(db: Session, request:Request, employee_id: int):
        employee = (
            db.query(Employee)
            .filter(Employee.id == employee_id, Employee.status == 1)
            .first()
        )

        if not employee:
            return error_response("Employee not found", 404)

        emp_id = employee.id

        aadhaar = db.query(Aadhaar).filter(
            Aadhaar.emp_id == emp_id,
            Aadhaar.status == 1
        ).first()

        pan = db.query(PAN).filter(
            PAN.emp_id == emp_id,
            PAN.status == 1
        ).first()

        qualification = db.query(Qualification).filter(
            Qualification.emp_id == emp_id,
            Qualification.status == 1
        ).first()

        resume = db.query(Resume).filter(
            Resume.emp_id == emp_id,
            Resume.status == 1
        ).first()

        address = db.query(AddressProof).filter(
            AddressProof.emp_id == emp_id,
            AddressProof.status == 1
        ).first()
        
        #encrypted_id = encrypt_id({"employee_id": employee.id})
        encrypted_id=encrypt_id(employee.id)

        return success_response(
            "Employee details",
            {
                #"id": employee.id,
                "id":encrypted_id,
                "emp_id": employee.emp_id,
                "emp_name": employee.emp_name,

                "aadhaar": aadhaar is not None,
                "aadhaar_details": {
                    "id":aadhaar.id,
                    "full_name": aadhaar.full_name,
                    "date_of_birth_or_yob": str(aadhaar.date_of_birth_or_yob),
                    "gender": aadhaar.gender,
                    "aadhaar_number": mask_aadhaar(aadhaar.aadhaar_number),
                    "address": aadhaar.address,
                    "file_path": f'{request.state.base_url}/{aadhaar.file_path}',
                } if aadhaar else None,

                "pan": pan is not None,
                "pan_details": {
                    "id":pan.id,
                    "pan_number": mask_pan(pan.pan_number),
                    "full_name": pan.full_name,
                    "date_of_birth": str(pan.date_of_birth),
                    "father_name": pan.father_name,
                    "file_path": f'{request.state.base_url}/{pan.file_path}',
                } if pan else None,

                "qualification": qualification is not None,
                "qualification_details": {
                    "id":qualification.id,
                    "highest_qualification": qualification.highest_qualification,
                    "institute_name": qualification.institute_name,
                    "specialization": qualification.specialization,
                    "year_of_passing": qualification.year_of_passing,
                    "file_path": f'{request.state.base_url}/{qualification.file_path}',
                } if qualification else None,

                "resume": resume is not None,
                "resume_details": {
                    "id":resume.id,
                    "full_name": resume.full_name,
                    "email": resume.email,
                    "mobile_number": resume.mobile_number,
                    "total_experience_years": resume.total_experience_years,
                    "last_company": resume.last_company,
                    "skills": resume.skills,
                    "file_path": f'{request.state.base_url}/{resume.file_path}',
                } if resume else None,

                "address_proof": address is not None,
                "address_proof_details": {
                    "id":address.id,
                    "full_name": address.full_name,
                    "address": address.address,
                    "document_name": address.document_name,
                    "issue_date": str(address.issue_date),
                    "file_path": f'{request.state.base_url}/{address.file_path}',
                } if address else None
            }
        )

# ------------------ List Employees ------------------

    @staticmethod
    def list_employees(
        db: Session,
        search: str = "",
        filter:str ="",
        sort: str = "createdAt",
        order: str = "DESC",
        limit: int = 10,
        offset: int = 0,
        
    ):

        query = (
            db.query( Employee, Aadhaar, PAN, Qualification, Resume, AddressProof)
            .outerjoin(Aadhaar, (Aadhaar.emp_id == Employee.id) & (Aadhaar.status == 1))
            .outerjoin(PAN, (PAN.emp_id == Employee.id) & (PAN.status == 1))
            .outerjoin(Qualification, (Qualification.emp_id == Employee.id) & (Qualification.status == 1))
            .outerjoin(Resume, (Resume.emp_id == Employee.id) & (Resume.status == 1))
            .outerjoin(AddressProof, (AddressProof.emp_id == Employee.id) & (AddressProof.status == 1))
            .filter(Employee.status == 1)
        )

        #SEARCH (emp_name or emp_id)
        if search:
            query = query.filter(
                or_( Employee.emp_name.ilike(f"%{search}%"), Employee.emp_id.ilike(f"%{search}%") )
            )

        #SORTING
        sort_column = getattr(Employee, sort, Employee.createdAt)

        if order.upper() == "ASC":
            query = query.order_by(asc(sort_column))
        else:
            query = query.order_by(desc(sort_column))
      
        rows = query.all()

        filtered_result = []
        for emp, aadhaar, pan, qualification, resume, address in rows:
            # KYC STATUS
            kyc_status = all([ bool(aadhaar), bool(pan), bool(qualification), bool(resume), bool(address) ])
            
            # ---------------- FILTER APPLY ----------------
        
            if filter and filter.lower() == "Approved" and not kyc_status:
                 continue

            if filter and filter.lower() == "Pending" and kyc_status:
                continue

            filtered_result.append({
                "id": encrypt_id(emp.id),
                "emp_id": emp.emp_id,
                "emp_name": emp.emp_name,
                "createdAt": EmployeeService._format_datetime(emp.createdAt),
                "aadhaar": bool(aadhaar),
                "pan": bool(pan),
                "qualification": bool(qualification),
                "resume": bool(resume),
                "address_proof": bool(address),
                "kyc_status": kyc_status
                
            })
            
        total_records =len(filtered_result)
        paginated_result = filtered_result[offset:offset + limit]
            
        return success_response(
            "Employee list",
            {
                "items": paginated_result,
                "pagination": {
                    # "limit": limit,
                    # "offset": offset,
                    "total_records": total_records
                }
            }
        )
# ------------------ List Basic Employees ------------------
    @staticmethod
    def list_basic_employees(db: Session):
        employees = (
            db.query(Employee)
            .filter(Employee.status == 1)
            .order_by(Employee.createdAt.desc())
            .all()
        )
        
        result = []
        for emp in employees:
            result.append({
                # "id": emp.id,
                "id": encrypt_id(emp.id),
                "emp_id": emp.emp_id,
                "emp_name": emp.emp_name,
                "status": emp.status
            })

        return success_response("Employee list", result)
    
    # ------------------ Delete Employee ------------------
    @staticmethod
    def delete_employee(db: Session, encrypted_id: str):

    # Decrypt employee id
        try:
            employee_id = decrypt_id(encrypted_id)
        except Exception:
            return error_response("Invalid encrypted id", 400)

    # Find employee
        employee = (
            db.query(Employee)
            .filter(Employee.id == employee_id, Employee.status == 1)
            .first()
        )

        if not employee:
            return error_response("Employee not found", 404)

        emp_id = employee.emp_id  # string emp_id used in documents

    # ------------------ delete documents ------------------
        db.query(Aadhaar).filter(
            Aadhaar.emp_id == emp_id,
            Aadhaar.status == 1
        ).update({"status": -1})

        db.query(PAN).filter(
            PAN.emp_id == emp_id,
            PAN.status == 1
        ).update({"status": -1})

        db.query(Qualification).filter(
            Qualification.emp_id == emp_id,
            Qualification.status == 1
        ).update({"status": -1})

        db.query(Resume).filter(
            Resume.emp_id == emp_id,
            Resume.status == 1
        ).update({"status": -1})

        db.query(AddressProof).filter(
            AddressProof.emp_id == emp_id,
            AddressProof.status == 1
        ).update({"status": -1})

    # ------------------ delete employee ------------------
        employee.status = -1

        db.commit()

        return success_response(
            "Employee and documents deleted successfully",
            {
                "id": encrypted_id,
                "emp_id": emp_id
            }
        )

