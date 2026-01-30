# coding: utf-8

from typing import ClassVar, Dict, List, Tuple  # noqa: F401
from typing import Optional

from openapi_server.models.notification_sending import NotificationSending


class BaseNotificationApi:
    subclasses: ClassVar[Tuple] = ()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        BaseNotificationApi.subclasses = BaseNotificationApi.subclasses + (cls,)
    async def get_notifications(
        self,
        context,
        authorization: str,
        number: int,
        page: int,
    ) -> List[NotificationSending]:
        """"""
        ...
