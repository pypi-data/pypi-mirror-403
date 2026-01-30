import logging
from abc import abstractmethod
from typing import Any, Iterable, Optional

from .result import IqlResult

logger = logging.getLogger(__name__)


class IqlDatabase:
    @abstractmethod
    def execute_query(
        self,
        query: str,
        completed_results: Iterable[IqlResult],
        raw: bool = False,
        parameters: Optional[Iterable[Any]] = None,
    ) -> Optional[IqlResult]:
        pass

    @abstractmethod
    def get_connection(self) -> Any:
        pass

    @abstractmethod
    def close_db(self):
        pass


class IqlDatabaseConnector:
    @abstractmethod
    def create_database(self, **kwargs: dict[str, Any]) -> IqlDatabase:
        pass

    @abstractmethod
    def create_database_from_con(self, con: Any) -> IqlDatabase:
        pass
