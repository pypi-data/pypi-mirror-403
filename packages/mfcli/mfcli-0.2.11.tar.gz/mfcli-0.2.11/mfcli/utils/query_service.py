from typing import Type, List, Any

from mfcli.models.base import Base
from mfcli.utils.orm import Session


class QueryService:
    def __init__(self, db: Session):
        self._db = db

    def query_all(
            self,
            entity_type: Type[Base],
            filters: List[Any] | None = None,
            order_by: Any | None = None
    ) -> List[Base]:
        query = self._db.query(entity_type)
        if filters:
            query = query.filter(filters)
        if order_by:
            query = query.order_by(order_by)
        return query.all()
