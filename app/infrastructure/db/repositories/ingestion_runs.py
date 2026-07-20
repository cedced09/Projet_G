from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.infrastructure.db.models import IngestionRunModel


class IngestionRunRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def start(self, source: str) -> IngestionRunModel:
        model = IngestionRunModel(source=source)
        self._session.add(model)
        self._session.flush()
        return model

    def finish(
        self,
        run: IngestionRunModel,
        *,
        status: str,
        finished_at: datetime,
        items_seen: int,
        items_created: int,
        items_updated: int,
        error_details: list[dict[str, Any]],
    ) -> IngestionRunModel:
        run.status = status
        run.finished_at = finished_at
        run.items_seen = items_seen
        run.items_created = items_created
        run.items_updated = items_updated
        run.error_count = len(error_details)
        run.error_details = error_details or None
        self._session.flush()
        return run
