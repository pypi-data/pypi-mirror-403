from copy import deepcopy
from decimal import Decimal
from typing import Any

from foodeo_core.commands.repositories.interfaces import IRequestsTableRepository
from foodeo_core.dataclasses.result import ResultWithValue
from foodeo_core.shared.entities import ProductInCommand
from foodeo_core.shared.entities.commands import LocalCommand
from foodeo_core.shared.entities.corrections import ProductsInCorrections, CorrectionLocalRequest
from foodeo_core.shared.entities.irequests import ModifiersCommands, RequestItemsModifiers, ModifiersRequest, \
    IModifierRequest
from foodeo_core.shared.entities.requests_tables import RequestsTableRow
from foodeo_core.shared.enums import RequestEnum, FromClientEnum


class CreateCorrectionsFromCommand:
    def __init__(self, repository: IRequestsTableRepository):
        self.repository = repository

    def create_corrections(self, command_model: LocalCommand) -> ResultWithValue[CorrectionLocalRequest | None]:
        existing_request_tables: list[RequestsTableRow] = self._get_requests_tables(command_model)
        corrections: CorrectionLocalRequest | None = self._get_corrections(command_model, existing_request_tables)
        return ResultWithValue.success_value(corrections)

    def _get_requests_tables(self, command_model) -> list[RequestsTableRow]:
        existing_request_tables: list[RequestsTableRow] = self.repository.get_requests_tables_by_command(
            command_model.id)
        return existing_request_tables

    def _get_corrections(self, command_model: LocalCommand,
                         existing_request_tables: list[RequestsTableRow]) -> CorrectionLocalRequest | None:

        list_product: dict[str, Any] = self._get_corrections_products(command_model,
                                                                      existing_request_tables)

        products: list[ProductsInCorrections] = list_product.get('products')
        not_found_items = self._create_corrections_for_deleted_products(list_product.get("not_found_items"))
        products.extend(not_found_items)
        if not products:
            return None
        local_request: CorrectionLocalRequest = CorrectionLocalRequest(qr=command_model.qr,
                                                                       command_guests=command_model.command_guests,
                                                                       type=RequestEnum.local,
                                                                       command_id=command_model.id,
                                                                       from_client=FromClientEnum.web,
                                                                       details=command_model.details,
                                                                       products=products)
        return local_request

    def _create_corrections_for_deleted_products(self, existing_request_tables: list[RequestsTableRow]) -> list[
        ProductsInCorrections]:
        list_products: list[ProductsInCorrections] = []
        for request_table in existing_request_tables:
            list_modifiers: list[RequestItemsModifiers] = []
            modifiers_in_product: list[ModifiersCommands] = request_table.modifiers
            for modifier in modifiers_in_product:
                product: RequestItemsModifiers = self._get_modifier_from_product(modifier)
                list_modifiers.append(product)
            price: Decimal = Decimal(request_table.importe / request_table.qty).quantize(Decimal('.01'))
            list_products.append(
                ProductsInCorrections(qty=-request_table.qty, name=request_table.product_name,
                                      price=price, amount=request_table.importe,
                                      modifiers=list_modifiers,
                                      total_price=request_table.total_price,
                                      unit_price=0, id=request_table.product_id,
                                      ))
        return list_products

    def _get_modifier_from_product(self, modifier: ModifiersCommands) -> RequestItemsModifiers:
        return RequestItemsModifiers(**{

            "modifiers_id": modifier.modifiers_id,
            "modifiers_name": modifier.modifiers_name,
            "modifiers_image": modifier.modifiers_image,
            "max_value_modifiers": modifier.max_value_modifiers,
            "min_value_modifiers": modifier.min_value_modifiers,
            "options_id": modifier.options_id,
            "options_name": modifier.options_name,
            "options_image": modifier.options_image,
            "max_value_options": modifier.max_value_options,
            "min_value_options": modifier.min_value_options,
            "qty": modifier.qty,
            "price": modifier.price,
            "modifiers_child_id": modifier.modifiers_child_id,
            "modifiers_child_name": modifier.modifiers_child_name,
            "modifiers_child_image": modifier.modifiers_child_image,
            "max_value_modifiers_child": modifier.max_value_modifiers_child,
            "min_value_modifiers_child": modifier.min_value_modifiers_child,
            "options_child_id": modifier.options_child_id,
            "options_child_name": modifier.options_child_name,
            "options_child_image": modifier.options_child_image,
            "max_value_options_child": modifier.max_value_options_child,
            "min_value_options_child": modifier.min_value_options_child,
            "qty_child": modifier.qty_child,
            "price_child": modifier.price_child,
            "importe": modifier.importe,
            "importe_child": modifier.importe_child,
        })

    def _get_corrections_products(self, command_model: LocalCommand,
                                  existing_request_tables_in_database: list[RequestsTableRow]) -> dict[str, Any]:
        list_products: list[ProductsInCorrections] = []
        products_sent_in_command: list[ProductInCommand] = command_model.products
        list_not_found_items: list[RequestsTableRow] = []

        sent_with_request_table: dict[int, ProductInCommand] = {
            product.request_table: product
            for product in products_sent_in_command
            if product.request_table is not None
        }

        for item_in_database in existing_request_tables_in_database:
            item_data = sent_with_request_table.get(item_in_database.id)

            if item_data is None:
                list_not_found_items.append(item_in_database)
                continue

            if item_in_database.qty > item_data.qty:
                qty_diff: int = item_in_database.qty - item_data.qty
                list_products.append(
                    ProductsInCorrections(qty=-qty_diff, name=item_data.name,
                                          modifiers=item_in_database.modifiers,
                                          price=item_data.price, amount=item_data.amount,
                                          id=item_in_database.product_id,
                                          total_price=item_data.total_price,
                                          unit_price=item_data.unit_price, ))

            modifier_sent_by_request_table: dict[int, ModifiersRequest] = {
                modifier.modifiers_id: modifier
                for modifier in item_data.modifiers
            }
            list_modifier_by_product: list[IModifierRequest] = []
            for modifier_in_database in item_in_database.modifiers:
                modifier_data: ModifiersRequest = modifier_sent_by_request_table.get(modifier_in_database.modifiers_id)
                if not modifier_data:
                    continue
                if modifier_in_database.qty > modifier_data.qty:
                    qty_diff: int = modifier_in_database.qty - modifier_data.qty
                    mm = deepcopy(modifier_in_database)
                    mm.qty = -qty_diff
                    list_modifier_by_product.append(mm)
            if list_modifier_by_product:
                products_in_requests = ProductsInCorrections(qty=item_data.qty, name=item_data.name,
                                                             id=item_in_database.product_id, price=item_data.price,
                                                             amount=item_data.amount, total_price=item_data.total_price,
                                                             unit_price=item_data.unit_price,
                                                             modifiers=list_modifier_by_product)
                list_products.append(products_in_requests)

        return {"products": list_products, "not_found_items": list_not_found_items}
