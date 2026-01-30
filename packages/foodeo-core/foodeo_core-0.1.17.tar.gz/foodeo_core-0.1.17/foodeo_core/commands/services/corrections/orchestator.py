from dataclasses import dataclass

from foodeo_core.commands.repositories.interfaces import IRequestsTableRepository
from foodeo_core.dataclasses.result import ResultWithValue
from foodeo_core.shared.entities.commands import LocalCommand
from foodeo_core.shared.entities.corrections import CorrectionLocalRequest, ProductsInCorrections
from foodeo_core.shared.entities.requests_tables import RequestsTableRow
from foodeo_core.shared.enums import RequestEnum, FromClientEnum
from .deleted_products import DeletedProductsNegativeDeltaService
from .modifiers_tree_delta import build_modifiers_tree_negative_delta_service, ModifierNegativeDeltaService
from .product_qty_delta import ProductQtyNegativeDeltaService


@dataclass(frozen=True)
class CreateCorrectionsFromCommandOrchestrator:
    repository: IRequestsTableRepository
    product_qty_service: ProductQtyNegativeDeltaService
    modifiers_tree_service: ModifierNegativeDeltaService
    deleted_products_service: DeletedProductsNegativeDeltaService

    def create_corrections(self, command_model: LocalCommand) -> ResultWithValue[CorrectionLocalRequest | None]:
        existing = self.repository.get_requests_tables_by_command(command_model.id)
        corrections = self._build(command_model, existing)
        return ResultWithValue.success_value(corrections)

    def _build(self, command_model: LocalCommand, existing: list[RequestsTableRow]) -> CorrectionLocalRequest | None:
        products_sent = command_model.products

        sent_by_row_id = {
            p.request_table: p for p in products_sent if p.request_table is not None
        }

        out: list[ProductsInCorrections] = []
        not_found: list[RequestsTableRow] = []

        for db_row in existing:
            cmd_product = sent_by_row_id.get(db_row.id)
            if cmd_product is None:
                not_found.append(db_row)
                continue

            # A) delta negativo del qty del producto (snapshot DB modifiers)
            prod_delta = self.product_qty_service.build_delta(db_row, cmd_product)
            if prod_delta:
                out.append(prod_delta)

            # B) delta negativo del árbol de modifiers/options
            modifiers_delta = self.modifiers_tree_service.diff(
                db=db_row.modifiers,
                cmd=cmd_product.modifiers,
            )
            if modifiers_delta:
                # contrato: para changes de modifiers, el producto va con qty vigente (cmd)
                out.append(
                    ProductsInCorrections(
                        qty=cmd_product.qty,
                        name=cmd_product.name,
                        id=db_row.product_id,
                        price=cmd_product.price,
                        amount=cmd_product.amount,
                        total_price=cmd_product.total_price,
                        unit_price=cmd_product.unit_price,
                        modifiers=modifiers_delta,
                    )
                )

        # C) eliminados
        out.extend(self.deleted_products_service.build(not_found))

        if not out:
            return None

        return CorrectionLocalRequest(
            qr=command_model.qr,
            command_guests=command_model.command_guests,
            type=RequestEnum.local,
            command_id=command_model.id,
            from_client=FromClientEnum.web,
            details=command_model.details,
            products=out,
        )


def build_create_corrections_orchestrator(
        repository: IRequestsTableRepository) -> CreateCorrectionsFromCommandOrchestrator:
    return CreateCorrectionsFromCommandOrchestrator(
        repository=repository,
        product_qty_service=ProductQtyNegativeDeltaService(),
        modifiers_tree_service=build_modifiers_tree_negative_delta_service(),
        deleted_products_service=DeletedProductsNegativeDeltaService(),
    )
