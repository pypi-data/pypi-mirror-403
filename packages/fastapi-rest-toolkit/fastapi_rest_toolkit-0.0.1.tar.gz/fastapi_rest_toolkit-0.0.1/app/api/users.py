from sqlalchemy_crud_plus import CRUDPlus

from app.db.redis import redis_client
from app.fastapi_rest_toolkit.viewset import ViewSet
from app.fastapi_rest_toolkit.service import CRUDService
from app.fastapi_rest_toolkit.permissions import IsAuthenticated, AllowAny
from app.fastapi_rest_toolkit.throttle import (
    AsyncRedisSimpleRateThrottle,
)
from app.models.user import User
from app.schemas.user import UserRead, UserCreate, UserUpdate


class UserViewSet(ViewSet):
    read_schema = UserRead
    create_schema = UserCreate
    update_schema = UserUpdate

    # Demo: 默认需要登录。你想开放注册可改成 AllowAny
    permission_classes = (
        AllowAny,
        IsAuthenticated,
    )

    search_fields = ("email", "name")
    ordering_fields = ("id", "email", "name", "created_at")
    # throttle_classes = (AnonRateThrottle,)
    # AnonRateThrottle.THROTTLE_RATES = {
    #     'anon': '50/minute',
    # }
    throttle_classes = (AsyncRedisSimpleRateThrottle(redis=redis_client),)

    def __init__(self):
        user_crud = CRUDPlus(User)
        self.service = CRUDService(crud=user_crud, model=User)
