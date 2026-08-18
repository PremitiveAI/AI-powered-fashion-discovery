from sqlalchemy.orm import Session
from app.models.stores_model import Stores
from app.utils.response import error_response


class Validation:

    @staticmethod
    def validate_products(db: Session, products_id: list[int]):
        """
        Check if all product ids exist in products table
        """
        if not products_id:
            return error_response("products_id is required", 400)

        existing_products = (
            db.query(Stores.id)
            .filter(Stores.id.in_(products_id))
            .all()
        )

        existing_ids = {p.id for p in existing_products}
        missing_ids = set(products_id) - existing_ids

        if missing_ids:
            return error_response(
                f"Invalid product ids: {list(missing_ids)}",
                400
            )

        return None

    @staticmethod
    def validate_store_type(store_type: str):
        allowed = ["ONLINE", "OFFLINE", "BOTH"]
        if store_type.upper() not in allowed:
            return error_response(
                "store_type must be ONLINE, OFFLINE or BOTH",
                400
            )
        return None
