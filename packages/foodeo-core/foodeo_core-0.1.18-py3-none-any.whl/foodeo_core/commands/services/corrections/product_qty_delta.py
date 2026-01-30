from typing import Optional

from foodeo_core.shared.entities.commands import ProductInCommand
from foodeo_core.shared.entities.corrections import ProductsInCorrections
from foodeo_core.shared.entities.requests_tables import RequestsTableRow


class ProductQtyNegativeDeltaService:
    """
    Crea una línea de corrección cuando BAJA el qty del producto.
    - qty: delta negativo
    - modifiers: snapshot de DB (como estaba)
    """

    def build_delta(
            self,
            db_row: RequestsTableRow,
            cmd_product: ProductInCommand,
    ) -> Optional[ProductsInCorrections]:
        if db_row.qty <= cmd_product.qty:
            return None

        diff = db_row.qty - cmd_product.qty  # positivo
        return ProductsInCorrections(
            qty=-diff,
            name=cmd_product.name,
            id=db_row.product_id,
            price=cmd_product.price,
            amount=cmd_product.amount,
            total_price=cmd_product.total_price,
            unit_price=cmd_product.unit_price,
            modifiers=db_row.modifiers,  # <- snapshot DB
        )
