from sqlalchemy.orm import Session
from app.services.employee_service import EmployeeService
from app.utils.crypto import decrypt_id
from app.utils.response import error_response

class EmployeeController:

    @staticmethod
    def create(db: Session, payload):
        return EmployeeService.create_employee(db, payload.dict())

    @staticmethod
    def get_details(db, request, encrypted_id: str):
        try:
            employee_id = decrypt_id(encrypted_id)

            if not employee_id:
                return error_response("Invalid encrypted id", 400)

        except Exception:
            return error_response("Invalid encrypted id", 400)

        return EmployeeService.get_employee_details(db, request, employee_id)
  
    @staticmethod
    def list(db: Session, payload):
        return EmployeeService.list_employees(
            db,
            search=payload.search,
            filter=payload.filter,
            sort=payload.sort,
            order=payload.order,
            limit=payload.limit,
            offset=payload.offset
        )
        
    @staticmethod
    def list_basic(db: Session):
        return EmployeeService.list_basic_employees(db)
