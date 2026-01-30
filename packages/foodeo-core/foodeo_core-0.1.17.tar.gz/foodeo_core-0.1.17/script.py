from decimal import Decimal
from typing import Iterable

from foodeo_core.commands.repositories.interfaces import IRequestsTableRepository
from foodeo_core.commands.services.corrections.orchestator import build_create_corrections_orchestrator
from foodeo_core.shared.entities import ProductInCommand
from foodeo_core.shared.entities.commands import LocalCommand
from foodeo_core.shared.entities.irequests import ModifiersRequest, IOptionRequest, IModifierChildRequest, \
    IOptionChildRequest
from foodeo_core.shared.entities.requests_tables import RequestsTableRow


# -------------------------
# Fake repo (igual que tests)
# -------------------------

class FakeRepo(IRequestsTableRepository):
    def __init__(self, rows: list[RequestsTableRow]):
        self._rows = rows

    def get_requests_tables_by_command(self, command_id: int):
        return self._rows


# -------------------------
# Builders (igual que tests)
# -------------------------

def make_option_child(option_id: int, qty: int) -> IOptionChildRequest:
    return IOptionChildRequest.model_construct(id=option_id, qty=qty)


def make_modifier_child(child_id: int, options: list[IOptionChildRequest]) -> IModifierChildRequest:
    return IModifierChildRequest.model_construct(id=child_id, options=options)


def make_option(option_id: int, qty: int, modifiers_child: list[IModifierChildRequest] | None = None) -> IOptionRequest:
    return IOptionRequest.model_construct(id=option_id, qty=qty, modifiers=modifiers_child or [])


def make_modifier_with_options(modifiers_id: int, options: list[IOptionRequest]) -> ModifiersRequest:
    return ModifiersRequest.model_construct(modifiers_id=modifiers_id, options=options)


def make_request_table_row(
        *,
        row_id: int,
        product_id: int,
        qty: int,
        modifiers: list[ModifiersRequest] | None = None,
        product_name: str = "Prod DB",
        importe: Decimal = Decimal("10.00"),
        total_price: Decimal = Decimal("10.00"),
) -> RequestsTableRow:
    return RequestsTableRow.model_construct(
        id=row_id,
        product_id=product_id,
        qty=qty,
        modifiers=modifiers or [],
        product_name=product_name,
        importe=importe,
        total_price=total_price,
    )


def make_product_in_command(
        *,
        request_table: int | None,
        qty: int,
        name: str = "Prod CMD",
        modifiers: list[ModifiersRequest] | None = None,
        price: Decimal = Decimal("1.00"),
        amount: Decimal = Decimal("1.00"),
        total_price: Decimal = Decimal("1.00"),
        unit_price: Decimal = Decimal("1.00"),
) -> ProductInCommand:
    return ProductInCommand.model_construct(
        request_table=request_table,
        qty=qty,
        name=name,
        modifiers=modifiers or [],
        price=price,
        amount=amount,
        total_price=total_price,
        unit_price=unit_price,
    )


def make_command(*, command_id: int = 1, products: list[ProductInCommand] | None = None) -> LocalCommand:
    return LocalCommand.model_construct(
        id=command_id,
        products=products or [],
        qr="QR",
        command_guests=2,
        details="details",
    )


# -------------------------
# Pretty print del resultado
# -------------------------

def _indent(level: int) -> str:
    return "  " * level


def print_corrections_tree(result) -> None:
    """
    result: ResultWithValue[CorrectionLocalRequest|None]
    Imprime en árbol:
      Product qty
        Modifier
          Option qty
            ModifierChild
              OptionChild qty
    """
    print(f"success={getattr(result, 'success', None)}")
    value = getattr(result, "value", None)
    if not value:
        print("value=None")
        return

    print("value=CorrectionLocalRequest")
    for p in value.products:
        print(f"- Product(id={getattr(p, 'id', None)}, name={getattr(p, 'name', None)}, qty={getattr(p, 'qty', None)})")
        modifiers = getattr(p, "modifiers", None) or []
        for m in modifiers:
            print(f"{_indent(1)}- Modifier(modifiers_id={getattr(m, 'modifiers_id', None)})")
            options = getattr(m, "options", None) or []
            for o in options:
                print(f"{_indent(2)}- Option(id={getattr(o, 'id', None)}, qty={getattr(o, 'qty', None)})")
                childs = getattr(o, "modifiers", None) or []
                for ch in childs:
                    print(f"{_indent(3)}- ModifierChild(id={getattr(ch, 'id', None)})")
                    och = getattr(ch, "options", None) or []
                    for oc in och:
                        print(
                            f"{_indent(4)}- OptionChild(id={getattr(oc, 'id', None)}, qty={getattr(oc, 'qty', None)})")


# -------------------------
# Escenarios QA
# -------------------------

def scenario_1_product_qty_reduce_and_option_reduce():
    """
    DB: product qty 5, option 70 qty 5
    CMD: product qty 3, option 70 qty 2
    Esperado:
      - línea producto qty=-2
      - línea modifiers (qty contextual=3) con option 70 qty=-3
    """
    db_row = make_request_table_row(
        row_id=10,
        product_id=99,
        qty=5,
        modifiers=[make_modifier_with_options(7, [make_option(70, 5)])],
        product_name="Burger",
    )
    cmd_product = make_product_in_command(
        request_table=10,
        qty=3,
        name="Burger",
        modifiers=[make_modifier_with_options(7, [make_option(70, 2)])],
    )
    command = make_command(products=[cmd_product])
    return [db_row], command


def scenario_2_deleted_modifier_marks_all_options_negative():
    """
    DB: modifier 10 con options 7 qty 3, 8 qty 1
    CMD: no manda modifier 10
    Esperado: en línea modifiers -> option 7 qty=-3 y option 8 qty=-1
    """
    db_row = make_request_table_row(
        row_id=10,
        product_id=99,
        qty=2,
        modifiers=[make_modifier_with_options(10, [make_option(7, 3), make_option(8, 1)])],
        product_name="Burger",
    )
    cmd_product = make_product_in_command(request_table=10, qty=2, name="Burger", modifiers=[])
    command = make_command(products=[cmd_product])
    return [db_row], command


def scenario_3_deleted_option_child_negative():
    """
    DB: option 7 -> child 55 -> option_child 999 qty 5 y 1000 qty 2
    CMD: elimina option_child 999 (solo deja 1000)
    Esperado: option_child 999 qty=-5
    """
    db_row = make_request_table_row(
        row_id=10,
        product_id=99,
        qty=2,
        modifiers=[
            make_modifier_with_options(
                10,
                [
                    make_option(
                        7, 1,
                        modifiers_child=[
                            make_modifier_child(55, [make_option_child(999, 5), make_option_child(1000, 2)])
                        ],
                    )
                ],
            )
        ],
        product_name="Burger",
    )

    cmd_row_mod = make_modifier_with_options(
        10,
        [
            make_option(
                7, 1,
                modifiers_child=[
                    make_modifier_child(55, [make_option_child(1000, 2)])
                ],
            )
        ],
    )

    cmd_product = make_product_in_command(request_table=10, qty=2, name="Burger", modifiers=[cmd_row_mod])
    command = make_command(products=[cmd_product])
    return [db_row], command


def scenario_4_deleted_product():
    """
    DB: existe row_id=10 qty=4 Pizza
    CMD: no viene -> producto eliminado
    Esperado: línea con qty=-4
    """
    db_row = make_request_table_row(row_id=10, product_id=99, qty=4, product_name="Pizza", importe=Decimal("20.00"),
                                    total_price=Decimal("20.00"))
    command = make_command(products=[])
    return [db_row], command


SCENARIOS = {
    "1_product_qty_reduce_and_option_reduce": scenario_1_product_qty_reduce_and_option_reduce,
    "2_deleted_modifier_marks_all_options_negative": scenario_2_deleted_modifier_marks_all_options_negative,
    "3_deleted_option_child_negative": scenario_3_deleted_option_child_negative,
    "4_deleted_product": scenario_4_deleted_product,
}


def run_scenario(name: str) -> None:
    rows, command = SCENARIOS[name]()
    orchestrator = build_create_corrections_orchestrator(repository=FakeRepo(rows))
    res = orchestrator.create_corrections(command)
    print(f"\n=== SCENARIO: {name} ===")
    print_corrections_tree(res)


def main(selected: Iterable[str] | None = None) -> None:
    names = list(selected) if selected else list(SCENARIOS.keys())
    for name in names:
        run_scenario(name)


if __name__ == "__main__":
    # Si querés correr solo uno:
    # main(["1_product_qty_reduce_and_option_reduce"])
    main()
