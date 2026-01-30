from decimal import Decimal

from foodeo_core.shared.entities.corrections import ProductsInCorrections
from foodeo_core.shared.entities.irequests import ModifiersCommands, ModifiersRequest
from foodeo_core.shared.entities.requests_tables import RequestsTableRow


class DeletedProductsNegativeDeltaService:
    def build(self, db_rows: list[RequestsTableRow]) -> list[ProductsInCorrections]:
        out: list[ProductsInCorrections] = []
        for row in db_rows:
            list_modifiers: list[ModifiersRequest] = [
                self._map_modifier(m) for m in (row.modifiers or [])
            ]
            price = Decimal(row.importe / row.qty).quantize(Decimal(".01"))
            out.append(
                ProductsInCorrections(
                    qty=-row.qty,
                    name=row.product_name,
                    price=price,
                    amount=row.importe,
                    modifiers=list_modifiers,
                    total_price=row.total_price,
                    unit_price=0,
                    id=row.product_id,
                )
            )
        return out

    def _map_modifier(self, modifier: ModifiersCommands) -> ModifiersRequest:
        return ModifiersRequest(**{
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
