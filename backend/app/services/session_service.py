# app/services/session_service.py
from sqlalchemy.orm import Session
from sqlalchemy.dialects import mysql
from app.models.users_session_model import Sessions
from app.models.users_model import Users

def get_user_session(db: Session, session_token: str, dialing_code: int):
    auth_query = (
        db.query(
            Sessions.id,
            Sessions.session_token,
            Sessions.deviceId,
            Sessions.sessionType,
            Sessions.status,
            Sessions.createdAt.label("lastLoginTime"),
            Users.userId,
            Users.username,
            Users.dialingCode,
            Users.mobile,
            Users.status.label("userStatus"),
        )
        .join(Users, Sessions.userId == Users.userId)
        .filter(
            Sessions.session_token == session_token,
            Sessions.status == 1,
            Users.status != -1,
            Users.dialingCode == dialing_code,
        )
        .order_by(Sessions.id.desc())
        # .first()
    )

    # Print SQL string with bound values
    # print(auth_query.statement.compile(dialect=mysql.dialect(), compile_kwargs={"literal_binds": True}))

    # Then execute
    auth = auth_query.first()
    

    if not auth:
        return None
    
    result =  {
        "sessionId": auth.id,
        "session_token": auth.session_token,
        "deviceId": auth.deviceId,
        "sessionType": auth.sessionType,
        "lastLoginTime": auth.lastLoginTime,
        "sessionStatus": auth.status,
        "userId": auth.userId,
        "username": auth.username,
        "mobile": auth.mobile,
        "dialingCode": auth.dialingCode,
        "userStatus": auth.userStatus,
    }
    return result



# async def get_user_session(session_token: str, dialing_code: int):
#     from app.models import users_session_model
#     session_data = await users_session_model.filter( session_token=session_token).first()
#     print('session_data : ', session_data)
#     \nAttributeError: module \'app.models.users_session_model\' has no attribute \'filter\'\n'
#     return session_data

async def is_device_blocked(deviceId: str, user_role: str):
    # from app.models import BlockDeviceModel
    # record = await BlockDeviceModel.filter( deviceId=deviceId, type=user_role, status=1 ).first()
    # return True if record else False

    return False
