from abc import ABC, abstractmethod

from foodeo_core.shared.entities.requests_tables import RequestsTableRow


class IRequestsTableRepository(ABC):
    @abstractmethod
    def get_requests_tables_by_command(self, command_id: int) -> list[RequestsTableRow]:
        pass
