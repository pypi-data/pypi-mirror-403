# coding: utf-8

from typing import ClassVar, Dict, List, Tuple  # noqa: F401
from typing import Optional



class BaseSearchUserFeatureApi:
    subclasses: ClassVar[Tuple] = ()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        BaseSearchUserFeatureApi.subclasses = BaseSearchUserFeatureApi.subclasses + (cls,)
    async def get_user_features(
        self,
        context,
    ) -> None:
        ...
