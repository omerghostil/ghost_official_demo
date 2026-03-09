"""Analysis worker — ניתוח קולאז'ים ממתינים באמצעות OpenAI."""

import json
import logging
from datetime import datetime

from app.core.config import settings
from app.db.database import SessionLocal
from app.models.memory import Collage, Analysis
from app.services.analysis_service import analyze_collage
from app.services.memory_service import save_analysis_to_memory
from app.services.alert_service import evaluate_alerts, get_active_rules_text
from app.services.journal_service import log_event
from app.workers.base_worker import BaseWorker

logger = logging.getLogger(__name__)


class AnalysisWorker(BaseWorker):
    """worker ניתוח — מעבד קולאז'ים ממתינים."""

    def __init__(self):
        super().__init__(name="analysis_worker", interval_seconds=5.0)

    async def tick(self) -> None:
        db = SessionLocal()
        try:
            collage = (
                db.query(Collage)
                .filter(Collage.analysis_status == "pending")
                .order_by(Collage.created_at.asc())
                .first()
            )
            if not collage:
                return

            collage.analysis_status = "processing"
            db.commit()

            alert_rules_text = get_active_rules_text(db)
            result = await analyze_collage(collage.collage_path, alert_rules_text)

            analysis = Analysis(
                collage_id=collage.id,
                status="success" if result.success else "partial",
                summary_text=result.summary_text,
                timeline_events_json=json.dumps(result.timeline_events, ensure_ascii=False),
                detected_entities_json=json.dumps(result.detected_entities, ensure_ascii=False),
                dead_periods_json=json.dumps(result.dead_periods, ensure_ascii=False),
                critical_matches_json=json.dumps(result.critical_alert_matches, ensure_ascii=False),
                confidence_notes=result.confidence_notes,
                raw_response=result.raw_response,
                error_message=result.error if result.error else None,
                completed_at=datetime.utcnow(),
            )
            db.add(analysis)
            collage.analysis_status = "completed" if result.success else "partial"
            db.commit()
            db.refresh(analysis)

            if result.summary_text:
                people_count = 0
                vehicle_count = 0
                for entity in result.detected_entities:
                    entity_str = str(entity).lower()
                    if "person" in entity_str or "human" in entity_str:
                        people_count += 1
                    if "vehicle" in entity_str or "car" in entity_str:
                        vehicle_count += 1

                save_analysis_to_memory(
                    db=db,
                    analysis_id=analysis.id,
                    collage_start_ts=collage.start_ts,
                    collage_end_ts=collage.end_ts,
                    summary_text=result.summary_text,
                    detected_entities=result.detected_entities,
                    people_count=people_count,
                    vehicle_count=vehicle_count,
                    critical_matches=result.critical_alert_matches,
                )

            if result.critical_alert_matches:
                evaluate_alerts(db, result.critical_alert_matches, analysis.id)

            log_event("analysis_success" if result.success else "analysis_partial", {
                "collage_id": collage.id,
                "analysis_id": analysis.id,
            })

        except Exception as e:
            logger.error(f"שגיאה בניתוח: {e}")
            log_event("analysis_failed", {"error": str(e)})
        finally:
            db.close()
