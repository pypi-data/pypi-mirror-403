# coding: utf-8

from typing import ClassVar, Dict, List, Tuple  # noqa: F401
from typing import Optional



class BaseSearchUserApi:
    subclasses: ClassVar[Tuple] = ()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        BaseSearchUserApi.subclasses = BaseSearchUserApi.subclasses + (cls,)
    async def get_user(
        self,
        context,
        userId: int,
    ) -> None:
        """"""
        ...
