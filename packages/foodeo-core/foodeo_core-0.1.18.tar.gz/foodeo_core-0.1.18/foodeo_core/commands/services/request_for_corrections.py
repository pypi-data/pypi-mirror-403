from copy import deepcopy

from foodeo_core.commands.repositories.interfaces import IRequestsTableRepository
from foodeo_core.dataclasses.result import ResultWithValue
from foodeo_core.shared.entities import ProductInRequest, LocalRequest, ProductInCommand
from foodeo_core.shared.entities.commands import LocalCommand
from foodeo_core.shared.entities.irequests import ModifiersRequest, IModifierRequest
from foodeo_core.shared.entities.requests_tables import RequestsTableRow
from foodeo_core.shared.enums import RequestEnum, FromClientEnum


class CreateRequestForCorrectionsFromCommand:
    def __init__(self, repository: IRequestsTableRepository):
        self.repository = repository

    def create_request(self, command_model: LocalCommand) -> ResultWithValue[LocalRequest | None]:
        existing_request_tables: list[RequestsTableRow] = self._get_requests_tables(command_model)
        request: LocalRequest | None = self._get_request(command_model, existing_request_tables)
        return ResultWithValue.success_value(request)

    def _get_requests_tables(self, command_model: LocalCommand) -> list[RequestsTableRow]:
        existing_request_tables: list[RequestsTableRow] = self.repository.get_requests_tables_by_command(
            command_model.id)
        return existing_request_tables

    def _get_request(self, command_model: LocalCommand,
                     existing_request_tables: list[RequestsTableRow]) -> LocalRequest | None:

        list_product: list[ProductInRequest] = self._get_requests_products(command_model,
                                                                           existing_request_tables)
        if not list_product:
            return None
        local_request: LocalRequest = LocalRequest(qr=command_model.qr,
                                                   command_guests=command_model.command_guests,
                                                   type=RequestEnum.local,
                                                   command_id=command_model.id,
                                                   from_client=FromClientEnum.web,
                                                   details=command_model.details,
                                                   products=list_product)
        return local_request

    def _get_requests_products(self, local_request: LocalCommand,
                               existing_request_tables_in_database: list[RequestsTableRow]) -> list[ProductInRequest]:
        list_products: list[ProductInRequest] = []
        products_sent_in_command: list[ProductInCommand] = local_request.products

        sent_by_request_table: dict[int, ProductInCommand] = {
            product.request_table: product
            for product in products_sent_in_command
            if product.request_table is not None
        }

        for item_in_database in existing_request_tables_in_database:
            item_data: ProductInCommand = sent_by_request_table.get(item_in_database.id)
            if not item_data:
                continue
            if item_in_database.qty < item_data.qty:
                qty_diff: int = item_data.qty - item_in_database.qty
                products_in_requests = ProductInRequest(qty=qty_diff, name=item_data.name,
                                                        id=item_in_database.product_id, price=item_data.price,
                                                        amount=item_data.amount, total_price=item_data.total_price,
                                                        unit_price=item_data.unit_price, )
                list_products.append(products_in_requests)

            modifier_sent_by_request_table: dict[int, ModifiersRequest] = {
                modifier.modifiers_id: modifier
                for modifier in item_data.modifiers
            }
            list_modifier_by_product: list[IModifierRequest] = []
            for modifier_in_database in item_in_database.modifiers:
                modifier_data: ModifiersRequest = modifier_sent_by_request_table.get(modifier_in_database.modifiers_id)
                if not modifier_data:
                    continue
                if modifier_in_database.qty < modifier_data.qty:
                    qty_diff: int = modifier_data.qty - modifier_in_database.qty
                    mm = deepcopy(modifier_in_database)
                    mm.qty = -qty_diff
                    list_modifier_by_product.append(mm)
            if list_modifier_by_product:
                products_in_requests = ProductInRequest(qty=item_in_database.qty, name=item_data.name,
                                                        id=item_in_database.product_id, price=item_data.price,
                                                        amount=item_data.amount, total_price=item_data.total_price,
                                                        unit_price=item_data.unit_price,
                                                        modifiers=list_modifier_by_product)
                list_products.append(products_in_requests)

        return list_products
