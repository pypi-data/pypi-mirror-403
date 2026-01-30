from dataclasses import dataclass
from decimal import Decimal
from typing import Optional, List

from foodeo_core.commands.services.request_for_corrections import CreateRequestForCorrectionsFromCommand
from foodeo_core.shared.entities import ProductInCommand
from foodeo_core.shared.entities import ProductInRequest
from foodeo_core.shared.entities.requests_tables import RequestsTableRow
from foodeo_core.shared.enums import RequestEnum, FromClientEnum


# ---------
# Fakes mínimos para test unitario
# ---------
@dataclass
class FakeLocalCommand:
    id: int
    qr: str
    command_guests: Optional[int]
    details: str
    products: List[ProductInCommand]


class FakeRequestsTableRepository:
    def __init__(self, rows: list[RequestsTableRow]):
        self._rows = rows

    def get_requests_tables_by_command(self, command_id: int) -> list[RequestsTableRow]:
        # En unit tests no usamos command_id, pero lo dejamos por firma.
        return list(self._rows)


# Helpers
def make_product_in_command(
        *,
        request_table: Optional[int],
        qty: int,
        name: str = "Prod",
        product_id: Optional[int] = None,
) -> ProductInCommand:
    # Nota: ProductInCommand hereda de IProductsRequest, exige varios campos.
    # Completa los mínimos exigidos por tu modelo.
    return ProductInCommand(
        request_table=request_table,
        qty=qty,
        name=name,
        price=Decimal("10"),
        amount=Decimal("10"),
        total_price=Decimal("10"),
        unit_price=Decimal("10"),
        modifiers=[],
        id=product_id,  # en tu servicio usas product_id desde RequestsTableRow, no este id
    )


def assert_product_in_request(p: ProductInRequest, *, qty: int, product_id: int):
    assert p.qty == qty
    assert p.id == product_id


# ---------
# Tests
# ---------
def test_returns_none_when_no_corrections_needed():
    # DB tiene qty=2, command manda qty=2 => no hay diff
    repo = FakeRequestsTableRepository(
        rows=[RequestsTableRow(id=1, product_id=100, qty=2)]
    )
    service = CreateRequestForCorrectionsFromCommand(repo)

    cmd = FakeLocalCommand(
        id=10,
        qr="qr-1",
        command_guests=2,
        details="",
        products=[make_product_in_command(request_table=1, qty=2, name="A")],
    )

    result = service.create_request(cmd)
    assert result.is_success
    assert result.value is None


def test_creates_request_with_qty_diff_when_command_qty_greater():
    # DB qty=1, command qty=3 => diff 2
    repo = FakeRequestsTableRepository(
        rows=[RequestsTableRow(id=1, product_id=100, qty=1)]
    )
    service = CreateRequestForCorrectionsFromCommand(repo)

    cmd = FakeLocalCommand(
        id=10,
        qr="qr-1",
        command_guests=2,
        details="detalle",
        products=[make_product_in_command(request_table=1, qty=3, name="A")],
    )

    result = service.create_request(cmd)
    assert result.is_success
    req = result.value
    assert req is not None

    # Metadata base
    assert req.qr == "qr-1"
    assert req.command_id == 10
    assert req.type == RequestEnum.local
    assert req.from_client == FromClientEnum.web

    # Productos
    assert len(req.products) == 1
    p = req.products[0]
    assert_product_in_request(p, qty=2, product_id=100)


def test_ignores_db_rows_not_present_in_command():
    # DB tiene una row id=999 que no viene en command => se ignora sin explotar
    repo = FakeRequestsTableRepository(
        rows=[RequestsTableRow(id=999, product_id=200, qty=1)]
    )
    service = CreateRequestForCorrectionsFromCommand(repo)

    cmd = FakeLocalCommand(
        id=10,
        qr="qr-1",
        command_guests=None,
        details="",
        products=[make_product_in_command(request_table=1, qty=3, name="A")],
    )

    result = service.create_request(cmd)
    assert result.is_success
    assert result.value is None


def test_does_not_create_negative_or_zero_diff_when_command_qty_lower():
    # DB qty=5, command qty=3 => no corrección (tu servicio solo agrega)
    repo = FakeRequestsTableRepository(
        rows=[RequestsTableRow(id=1, product_id=100, qty=5)]
    )
    service = CreateRequestForCorrectionsFromCommand(repo)

    cmd = FakeLocalCommand(
        id=10,
        qr="qr-1",
        command_guests=2,
        details="",
        products=[make_product_in_command(request_table=1, qty=3, name="A")],
    )

    result = service.create_request(cmd)
    assert result.is_success
    assert result.value is None


def test_multiple_rows_creates_multiple_corrections():
    repo = FakeRequestsTableRepository(
        rows=[
            RequestsTableRow(id=1, product_id=100, qty=1),
            RequestsTableRow(id=2, product_id=101, qty=2),
        ]
    )
    service = CreateRequestForCorrectionsFromCommand(repo)

    cmd = FakeLocalCommand(
        id=10,
        qr="qr-1",
        command_guests=4,
        details="",
        products=[
            make_product_in_command(request_table=1, qty=2, name="A"),  # diff 1
            make_product_in_command(request_table=2, qty=5, name="B"),  # diff 3
        ],
    )

    result = service.create_request(cmd)
    assert result.is_success
    req = result.value
    assert req is not None
    assert len(req.products) == 2

    # orden no garantizado, comparamos por product_id
    by_id = {p.id: p for p in req.products}
    assert_product_in_request(by_id[100], qty=1, product_id=100)
    assert_product_in_request(by_id[101], qty=3, product_id=101)
