from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field

from foodeo_core.shared.entities.irequests import IProductsRequest, PRODUCT_TYPE_NAME, ModifiersCommands


class ProductInCommand(IProductsRequest):
    request_table: Optional[int] = None

    def get_type_name(self) -> PRODUCT_TYPE_NAME:
        return PRODUCT_TYPE_NAME.REQUEST_TABLE

    def get_id(self) -> int:
        return self.request_table


class RequestsTableRow(BaseModel):
    qty: int
    product_id: int
    id: int
    modifiers: list[ModifiersCommands] = Field(default_factory=list)
    product_name: Optional[str] = None
    importe: Decimal = Decimal(0)
    total_price: Decimal = Decimal(0)
