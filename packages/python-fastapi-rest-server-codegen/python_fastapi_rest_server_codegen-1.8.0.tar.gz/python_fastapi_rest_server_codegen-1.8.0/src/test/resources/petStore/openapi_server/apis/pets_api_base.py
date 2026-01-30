# coding: utf-8

from typing import ClassVar, Dict, List, Tuple  # noqa: F401
from typing import Optional

from openapi_server.models.error import Error
from openapi_server.models.pet import Pet


class BasePetsApi:
    subclasses: ClassVar[Tuple] = ()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        BasePetsApi.subclasses = BasePetsApi.subclasses + (cls,)
    async def create_pets(
        self,
        context,
    ) -> None:
        ...


    async def list_pets(
        self,
        context,
        limit: int,
    ) -> List[Pet]:
        ...


    async def show_pet_by_id(
        self,
        context,
        petId: str,
    ) -> Pet:
        ...
