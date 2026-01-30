import unittest
from decimal import Decimal

from foodeo_core.commands.repositories.interfaces import IRequestsTableRepository
from foodeo_core.commands.services.corrections.orchestator import build_create_corrections_orchestrator
from foodeo_core.shared.entities import ProductInCommand
from foodeo_core.shared.entities.commands import LocalCommand
from foodeo_core.shared.entities.irequests import IOptionRequest, IModifierChildRequest, IOptionChildRequest
from foodeo_core.shared.entities.irequests import ModifiersRequest
from foodeo_core.shared.entities.requests_tables import RequestsTableRow


class FakeRepo(IRequestsTableRepository):
    def __init__(self, rows: list[RequestsTableRow]):
        self._rows = rows

    def get_requests_tables_by_command(self, command_id: int):
        return self._rows


def make_modifier(modifiers_id: int, options: list[IOptionRequest]) -> ModifiersRequest:
    return ModifiersRequest.model_construct(modifiers_id=modifiers_id, options=options)


def make_option_child(option_id: int, qty: int) -> IOptionChildRequest:
    return IOptionChildRequest.model_construct(id=option_id, qty=qty)


def make_modifier_child(child_id: int, options: list[IOptionChildRequest]) -> IModifierChildRequest:
    return IModifierChildRequest.model_construct(id=child_id, options=options)


def make_option(option_id: int, qty: int, modifiers_child: list[IModifierChildRequest] | None = None) -> IOptionRequest:
    return IOptionRequest.model_construct(id=option_id, qty=qty, modifiers=modifiers_child or [])


def make_modifier_with_options(modifiers_id: int, options: list[IOptionRequest]) -> ModifiersRequest:
    # ModifiersRequest tiene options: list[IOptionRequest]
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


class TestCreateCorrectionsOrchestrator(unittest.TestCase):
    def test_returns_none_when_no_deltas(self):
        # DB == CMD en todo
        db_row = make_request_table_row(
            row_id=10,
            product_id=99,
            qty=2,
            modifiers=[make_modifier(modifiers_id=1, options=[])],
        )
        cmd_product = make_product_in_command(
            request_table=10,
            qty=2,
            modifiers=[make_modifier(modifiers_id=1, options=[])],
        )
        command = make_command(products=[cmd_product])

        orchestrator = build_create_corrections_orchestrator(repository=FakeRepo([db_row]))
        res = orchestrator.create_corrections(command)

        # Ajusta si tu ResultWithValue usa otros nombres:
        self.assertTrue(res.success)
        self.assertIsNone(res.value)

    def test_emits_two_lines_when_product_qty_and_option_qty_reduce(self):
        # DB qty 5 -> CMD qty 3 => producto delta (-2)
        # DB option qty 5 -> CMD 2 => option delta (-3)

        db_row = make_request_table_row(
            row_id=10,
            product_id=99,
            qty=5,
            modifiers=[
                make_modifier_with_options(
                    modifiers_id=7,
                    options=[make_option(option_id=70, qty=5)],
                )
            ],
        )

        cmd_product = make_product_in_command(
            request_table=10,
            qty=3,
            name="Burger",
            modifiers=[
                make_modifier_with_options(
                    modifiers_id=7,
                    options=[make_option(option_id=70, qty=2)],
                )
            ],
        )

        command = make_command(products=[cmd_product])

        orchestrator = build_create_corrections_orchestrator(repository=FakeRepo([db_row]))
        res = orchestrator.create_corrections(command)

        self.assertTrue(res.success)
        self.assertIsNotNone(res.value)

        products = res.value.products
        self.assertEqual(len(products), 2)

        # Línea A: delta de producto
        product_delta_line = next(p for p in products if p.qty == -2)
        self.assertEqual(product_delta_line.id, 99)
        # contrato: snapshot DB modifiers cuando cambia qty producto
        self.assertEqual(product_delta_line.modifiers, db_row.modifiers)

        # Línea B: delta de modifiers/options con qty contextual (cmd qty)
        modifiers_line = next(p for p in products if p.qty == cmd_product.qty and p.modifiers)
        self.assertEqual(modifiers_line.id, 99)

        # Debe contener modifier 7 con option 70 qty=-3
        m7 = next(m for m in modifiers_line.modifiers if m.modifiers_id == 7)
        opt70 = next(o for o in m7.options if o.id == 70)
        self.assertEqual(opt70.qty, -3)

    def test_deleted_product_generates_negative_qty_line(self):
        # DB row está pero no viene en command => eliminado
        db_row = make_request_table_row(
            row_id=10,
            product_id=99,
            qty=4,
            product_name="Pizza",
            importe=Decimal("20.00"),
            total_price=Decimal("20.00"),
            modifiers=[make_modifier(modifiers_id=1, options=[]), ],
        )
        command = make_command(products=[])

        orchestrator = build_create_corrections_orchestrator(repository=FakeRepo([db_row]))
        res = orchestrator.create_corrections(command)

        self.assertTrue(res.success)
        self.assertIsNotNone(res.value)

        # Debe existir una línea con qty=-4 y name=Pizza
        self.assertTrue(any(p.qty == -4 and p.name == "Pizza" for p in res.value.products))

    def test_deleted_modifier_marks_all_its_options_negative(self):
        # DB tiene modifier 10 con options: (7 qty 3), (8 qty 1)
        db_mod = make_modifier_with_options(
            modifiers_id=10,
            options=[
                make_option(7, 3),
                make_option(8, 1),
            ],
        )

        # CMD elimina modifier 10 (no lo manda)
        db_row = make_request_table_row(row_id=10, product_id=99, qty=2, modifiers=[db_mod])
        cmd_product = make_product_in_command(request_table=10, qty=2, name="Burger", modifiers=[])
        command = make_command(products=[cmd_product])

        orchestrator = build_create_corrections_orchestrator(repository=FakeRepo([db_row]))
        res = orchestrator.create_corrections(command)

        self.assertTrue(res.success)
        self.assertIsNotNone(res.value)

        # Línea de modifiers con qty contextual del producto
        modifiers_line = next(p for p in res.value.products if p.qty == cmd_product.qty and p.modifiers)
        m10 = next(m for m in modifiers_line.modifiers if m.modifiers_id == 10)

        self.assertEqual(len(m10.options), 2)
        opt7 = next(o for o in m10.options if o.id == 7)
        opt8 = next(o for o in m10.options if o.id == 8)

        self.assertEqual(opt7.qty, -3)
        self.assertEqual(opt8.qty, -1)

    def test_deleted_option_marks_option_qty_negative(self):
        # DB: modifier 10 tiene option 7 qty 3
        db_mod = make_modifier_with_options(
            modifiers_id=10,
            options=[make_option(7, 3)],
        )
        # CMD: modifier 10 existe pero sin option 7
        cmd_mod = make_modifier_with_options(
            modifiers_id=10,
            options=[],
        )

        db_row = make_request_table_row(row_id=10, product_id=99, qty=2, modifiers=[db_mod])
        cmd_product = make_product_in_command(request_table=10, qty=2, name="Burger", modifiers=[cmd_mod])
        command = make_command(products=[cmd_product])

        orchestrator = build_create_corrections_orchestrator(repository=FakeRepo([db_row]))
        res = orchestrator.create_corrections(command)

        self.assertTrue(res.success)
        self.assertIsNotNone(res.value)

        modifiers_line = next(p for p in res.value.products if p.qty == cmd_product.qty and p.modifiers)
        m10 = next(m for m in modifiers_line.modifiers if m.modifiers_id == 10)

        opt7 = next(o for o in m10.options if o.id == 7)
        self.assertEqual(opt7.qty, -3)

    def test_deleted_modifier_child_marks_all_option_children_negative(self):
        # DB: option 7 tiene child 55 con option_children 999 qty 5 y 1000 qty 2
        db_mod = make_modifier_with_options(
            modifiers_id=10,
            options=[
                make_option(
                    7, 1,
                    modifiers_child=[
                        make_modifier_child(
                            55,
                            options=[
                                make_option_child(999, 5),
                                make_option_child(1000, 2),
                            ],
                        )
                    ],
                )
            ],
        )

        # CMD: elimina child 55 (deja modifiers_child vacío)
        cmd_mod = make_modifier_with_options(
            modifiers_id=10,
            options=[
                make_option(7, 1, modifiers_child=[]),
            ],
        )

        db_row = make_request_table_row(row_id=10, product_id=99, qty=2, modifiers=[db_mod])
        cmd_product = make_product_in_command(request_table=10, qty=2, name="Burger", modifiers=[cmd_mod])
        command = make_command(products=[cmd_product])

        orchestrator = build_create_corrections_orchestrator(repository=FakeRepo([db_row]))
        res = orchestrator.create_corrections(command)

        self.assertTrue(res.success)
        self.assertIsNotNone(res.value)

        modifiers_line = next(p for p in res.value.products if p.qty == cmd_product.qty and p.modifiers)
        m10 = next(m for m in modifiers_line.modifiers if m.modifiers_id == 10)
        opt7 = next(o for o in m10.options if o.id == 7)

        ch55 = next(ch for ch in opt7.modifiers if ch.id == 55)
        oc999 = next(oc for oc in ch55.options if oc.id == 999)
        oc1000 = next(oc for oc in ch55.options if oc.id == 1000)

        self.assertEqual(oc999.qty, -5)
        self.assertEqual(oc1000.qty, -2)

    def test_deleted_option_child_marks_qty_negative(self):
        # DB: child 55 tiene option_child 999 qty 5 y 1000 qty 2
        db_mod = make_modifier_with_options(
            modifiers_id=10,
            options=[
                make_option(
                    7, 1,
                    modifiers_child=[
                        make_modifier_child(
                            55,
                            options=[make_option_child(999, 5), make_option_child(1000, 2)],
                        )
                    ],
                )
            ],
        )

        # CMD: elimina option_child 999 (solo deja 1000)
        cmd_mod = make_modifier_with_options(
            modifiers_id=10,
            options=[
                make_option(
                    7, 1,
                    modifiers_child=[
                        make_modifier_child(55, options=[make_option_child(1000, 2)]),
                    ],
                )
            ],
        )

        db_row = make_request_table_row(row_id=10, product_id=99, qty=2, modifiers=[db_mod])
        cmd_product = make_product_in_command(request_table=10, qty=2, name="Burger", modifiers=[cmd_mod])
        command = make_command(products=[cmd_product])

        orchestrator = build_create_corrections_orchestrator(repository=FakeRepo([db_row]))
        res = orchestrator.create_corrections(command)

        self.assertTrue(res.success)
        self.assertIsNotNone(res.value)

        modifiers_line = next(p for p in res.value.products if p.qty == cmd_product.qty and p.modifiers)
        m10 = next(m for m in modifiers_line.modifiers if m.modifiers_id == 10)
        opt7 = next(o for o in m10.options if o.id == 7)
        ch55 = next(ch for ch in opt7.modifiers if ch.id == 55)

        oc999 = next(oc for oc in ch55.options if oc.id == 999)
        self.assertEqual(oc999.qty, -5)

    def test_emits_only_modifiers_line_when_only_options_reduce(self):
        # Producto igual, opción reduce => solo 1 línea (modifiers/options)
        db_row = make_request_table_row(
            row_id=10,
            product_id=99,
            qty=3,
            modifiers=[make_modifier_with_options(7, [make_option(70, 5)])],
        )
        cmd_product = make_product_in_command(
            request_table=10,
            qty=3,
            modifiers=[make_modifier_with_options(7, [make_option(70, 2)])],
        )
        command = make_command(products=[cmd_product])

        orchestrator = build_create_corrections_orchestrator(repository=FakeRepo([db_row]))
        res = orchestrator.create_corrections(command)

        self.assertTrue(res.success)
        self.assertIsNotNone(res.value)

        products = res.value.products
        self.assertEqual(len(products), 1)

        line = products[0]
        self.assertEqual(line.qty, 3)  # qty contextual
        m7 = next(m for m in line.modifiers if m.modifiers_id == 7)
        opt70 = next(o for o in m7.options if o.id == 70)
        self.assertEqual(opt70.qty, -3)

    def test_emits_only_product_line_when_only_product_qty_reduce(self):
        db_mod = make_modifier_with_options(7, [make_option(70, 5)])
        db_row = make_request_table_row(row_id=10, product_id=99, qty=5, modifiers=[db_mod])

        cmd_mod = make_modifier_with_options(7, [make_option(70, 5)])  # igual
        cmd_product = make_product_in_command(request_table=10, qty=3, modifiers=[cmd_mod])
        command = make_command(products=[cmd_product])

        orchestrator = build_create_corrections_orchestrator(repository=FakeRepo([db_row]))
        res = orchestrator.create_corrections(command)

        self.assertTrue(res.success)
        self.assertIsNotNone(res.value)

        products = res.value.products
        self.assertEqual(len(products), 1)

        line = products[0]
        self.assertEqual(line.qty, -2)
        self.assertEqual(line.modifiers, db_row.modifiers)  # snapshot DB

    def test_returns_none_when_only_positive_or_equal_changes(self):
        # option sube: 2->5, producto igual
        db_row = make_request_table_row(
            row_id=10,
            product_id=99,
            qty=3,
            modifiers=[make_modifier_with_options(7, [make_option(70, 2)])],
        )
        cmd_product = make_product_in_command(
            request_table=10,
            qty=3,
            modifiers=[make_modifier_with_options(7, [make_option(70, 5)])],
        )
        command = make_command(products=[cmd_product])

        orchestrator = build_create_corrections_orchestrator(repository=FakeRepo([db_row]))
        res = orchestrator.create_corrections(command)

        self.assertTrue(res.success)
        self.assertIsNone(res.value)

    def test_mix_delete_option_and_reduce_other_option_same_modifier(self):
        # DB: option 70 qty=5, option 71 qty=4
        db_mod = make_modifier_with_options(
            7,
            [make_option(70, 5), make_option(71, 4)],
        )
        db_row = make_request_table_row(row_id=10, product_id=99, qty=3, modifiers=[db_mod])

        # CMD: elimina 70, reduce 71 4->1
        cmd_mod = make_modifier_with_options(
            7,
            [make_option(71, 1)],
        )
        cmd_product = make_product_in_command(request_table=10, qty=3, modifiers=[cmd_mod])
        command = make_command(products=[cmd_product])

        orchestrator = build_create_corrections_orchestrator(repository=FakeRepo([db_row]))
        res = orchestrator.create_corrections(command)

        self.assertTrue(res.success)
        self.assertIsNotNone(res.value)

        line = next(p for p in res.value.products if p.qty == 3 and p.modifiers)
        m7 = next(m for m in line.modifiers if m.modifiers_id == 7)

        opt70 = next(o for o in m7.options if o.id == 70)
        opt71 = next(o for o in m7.options if o.id == 71)

        self.assertEqual(opt70.qty, -5)  # eliminado completo
        self.assertEqual(opt71.qty, -3)  # 4->1

    def test_deleted_modifier_with_no_options_produces_no_delta(self):
        db_mod = make_modifier_with_options(modifiers_id=10, options=[])
        db_row = make_request_table_row(row_id=10, product_id=99, qty=3, modifiers=[db_mod])

        cmd_product = make_product_in_command(request_table=10, qty=3, modifiers=[])  # modifier eliminado
        command = make_command(products=[cmd_product])

        orchestrator = build_create_corrections_orchestrator(repository=FakeRepo([db_row]))
        res = orchestrator.create_corrections(command)

        self.assertTrue(res.success)
        # Si no hay options que “quitar”, no hay corrección por modifiers.
        # (Si tu negocio quiere igual emitir el modifier, cambia este assert.)
        self.assertIsNone(res.value)

    def test_deleted_product_and_other_product_with_option_delta(self):
        db_rows = [
            make_request_table_row(row_id=10, product_id=99, qty=2, product_name="Pizza"),
            make_request_table_row(
                row_id=11,
                product_id=100,
                qty=3,
                modifiers=[make_modifier_with_options(7, [make_option(70, 5)])],
                product_name="Burger",
            ),
        ]

        cmd_product = make_product_in_command(
            request_table=11,
            qty=3,
            name="Burger",
            modifiers=[make_modifier_with_options(7, [make_option(70, 2)])],
        )
        command = make_command(products=[cmd_product])

        orchestrator = build_create_corrections_orchestrator(repository=FakeRepo(db_rows))
        res = orchestrator.create_corrections(command)

        self.assertTrue(res.success)
        self.assertIsNotNone(res.value)

        # Debe incluir delete del row_id=10 => qty=-2 (Pizza)
        self.assertTrue(any(p.name == "Pizza" and p.qty == -2 for p in res.value.products))
        # Debe incluir delta de option para Burger
        burger_line = next(p for p in res.value.products if p.id == 100 and p.modifiers)
        m7 = next(m for m in burger_line.modifiers if m.modifiers_id == 7)
        opt70 = next(o for o in m7.options if o.id == 70)
        self.assertEqual(opt70.qty, -3)
