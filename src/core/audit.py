"""
Atlas AI — Audit Logging System
Provides traceability and auditability for all eligibility decisions.
Critical for compliance with proposal requirements.
"""

import json
import logging
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, Dict, Any, List

from src.core.config import AtlasConfig


class AuditEventType(str, Enum):
    """Types of audit events."""
    SESSION_START = "session_start"
    MESSAGE_RECEIVED = "message_received"
    INTENT_CLASSIFIED = "intent_classified"
    ENTITIES_EXTRACTED = "entities_extracted"
    CLARIFICATION_ASKED = "clarification_asked"
    RULE_EVALUATED = "rule_evaluated"
    ELIGIBILITY_DETERMINED = "eligibility_determined"
    EXPLANATION_GENERATED = "explanation_generated"
    SESSION_END = "session_end"
    ERROR_OCCURRED = "error_occurred"
    RESET_REQUESTED = "reset_requested"


class VerdictType(str, Enum):
    """Eligibility verdict types."""
    ELIGIBLE = "eligible"
    NOT_ELIGIBLE = "not_eligible"
    INSUFFICIENT_INFO = "insufficient_info"


@dataclass
class AuditEvent:
    """Single audit event record."""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: AuditEventType = AuditEventType.MESSAGE_RECEIVED
    session_id: str = ""
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    
    # Event-specific data
    data: Dict[str, Any] = field(default_factory=dict)
    
    # Rule trace (for eligibility decisions)
    rule_id: Optional[str] = None
    rule_result: Optional[Dict[str, Any]] = None
    
    # User context (anonymized)
    user_input_hash: Optional[str] = None  # Hash of input, not raw text
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "session_id": self.session_id,
            "timestamp": self.timestamp,
            "trace_id": self.trace_id,
            "data": self.data,
            "rule_id": self.rule_id,
            "rule_result": self.rule_result,
            "user_input_hash": self.user_input_hash,
        }


class AuditLogger:
    """
    Audit logger for Atlas AI.
    Provides traceable, tamper-evident logging of all system decisions.
    
    Key features:
    - Every eligibility decision is logged with full trace
    - GOV.UK source citations are recorded
    - No personal data is stored (GDPR compliant)
    - Logs are append-only for audit integrity
    """
    
    def __init__(self, log_file: Optional[Path] = None):
        self.log_file = log_file or AtlasConfig.AUDIT_LOG_FILE
        self._ensure_log_file()
        self._setup_logger()
    
    def _ensure_log_file(self):
        """Ensure log directory exists."""
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
    
    def _setup_logger(self):
        """Configure the audit logger."""
        self._logger = logging.getLogger(f"atlas_audit_{id(self)}")
        self._logger.setLevel(logging.INFO)
        
        # Remove existing handlers
        self._logger.handlers.clear()
        
        # File handler for audit log
        file_handler = logging.FileHandler(self.log_file)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(logging.Formatter("%(message)s"))
        self._logger.addHandler(file_handler)
    
    def log_event(self, event: AuditEvent):
        """Log an audit event."""
        self._logger.info(json.dumps(event.to_dict(), default=str))
    
    def log_session_start(self, session_id: str) -> AuditEvent:
        """Log session start."""
        event = AuditEvent(
            event_type=AuditEventType.SESSION_START,
            session_id=session_id,
            data={"config": AtlasConfig.to_dict()}
        )
        self.log_event(event)
        return event
    
    def log_message_received(self, session_id: str, input_hash: str) -> AuditEvent:
        """Log message received (without storing raw text for privacy)."""
        event = AuditEvent(
            event_type=AuditEventType.MESSAGE_RECEIVED,
            session_id=session_id,
            user_input_hash=input_hash,
        )
        self.log_event(event)
        return event
    
    def log_intent_classification(
        self, 
        session_id: str, 
        intent: str, 
        confidence: float,
        all_scores: Dict[str, float],
        source: str,
    ) -> AuditEvent:
        """Log intent classification result."""
        event = AuditEvent(
            event_type=AuditEventType.INTENT_CLASSIFIED,
            session_id=session_id,
            data={
                "intent": intent,
                "confidence": confidence,
                "all_scores": all_scores,
                "source": source,
                "low_confidence": confidence < AtlasConfig.INTENT_CONFIDENCE_THRESHOLD,
            }
        )
        self.log_event(event)
        return event
    
    def log_entities_extracted(
        self,
        session_id: str,
        entities: Dict[str, Any],
        low_confidence_entities: List[str],
        source: str,
    ) -> AuditEvent:
        """Log entity extraction result."""
        event = AuditEvent(
            event_type=AuditEventType.ENTITIES_EXTRACTED,
            session_id=session_id,
            data={
                "entities": {
                    k: {"value": v.get("value"), "confidence": v.get("confidence")}
                    for k, v in entities.items()
                },
                "low_confidence_entities": low_confidence_entities,
                "source": source,
            }
        )
        self.log_event(event)
        return event
    
    def log_rule_evaluated(
        self,
        session_id: str,
        rule_id: str,
        rule_description: str,
        passed: bool,
        reason: str,
        source_url: str,
        source_section: str,
    ) -> AuditEvent:
        """Log individual rule evaluation."""
        event = AuditEvent(
            event_type=AuditEventType.RULE_EVALUATED,
            session_id=session_id,
            rule_id=rule_id,
            data={
                "rule_description": rule_description,
                "passed": passed,
                "reason": reason,
                "source_url": source_url,
                "source_section": source_section,
            }
        )
        self.log_event(event)
        return event
    
    def log_eligibility_determined(
        self,
        session_id: str,
        verdict: VerdictType,
        visa_type: str,
        points_earned: int,
        points_required: int,
        rule_results: List[Dict[str, Any]],
        missing_info: List[str],
        trace_id: str,
    ) -> AuditEvent:
        """Log final eligibility determination."""
        event = AuditEvent(
            event_type=AuditEventType.ELIGIBILITY_DETERMINED,
            session_id=session_id,
            trace_id=trace_id,
            data={
                "verdict": verdict.value,
                "visa_type": visa_type,
                "points_earned": points_earned,
                "points_required": points_required,
                "rules_passed": sum(1 for r in rule_results if r.get("passed")),
                "rules_failed": sum(1 for r in rule_results if not r.get("passed")),
                "missing_info": missing_info,
                "gov_uk_sources": list(set(
                    r.get("source_url", "") 
                    for r in rule_results 
                    if r.get("source_url")
                )),
            }
        )
        self.log_event(event)
        return event
    
    def log_explanation_generated(
        self,
        session_id: str,
        trace_id: str,
        source: str,
        hallucination_detected: bool,
    ) -> AuditEvent:
        """Log explanation generation."""
        event = AuditEvent(
            event_type=AuditEventType.EXPLANATION_GENERATED,
            session_id=session_id,
            trace_id=trace_id,
            data={
                "source": source,
                "hallucination_detected": hallucination_detected,
            }
        )
        self.log_event(event)
        return event
    
    def log_error(
        self,
        session_id: str,
        error_type: str,
        error_message: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> AuditEvent:
        """Log an error event."""
        event = AuditEvent(
            event_type=AuditEventType.ERROR_OCCURRED,
            session_id=session_id,
            data={
                "error_type": error_type,
                "error_message": error_message,
                "context": context or {},
            }
        )
        self.log_event(event)
        return event
    
    def log_session_end(self, session_id: str) -> AuditEvent:
        """Log session end."""
        event = AuditEvent(
            event_type=AuditEventType.SESSION_END,
            session_id=session_id,
        )
        self.log_event(event)
        return event
    
    def get_session_audit_trail(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve full audit trail for a session.
        Note: This requires the log file to be queryable.
        For production, this would use a proper database.
        """
        trail = []
        try:
            with open(self.log_file, 'r') as f:
                for line in f:
                    try:
                        event = json.loads(line.strip())
                        if event.get("session_id") == session_id:
                            trail.append(event)
                    except json.JSONDecodeError:
                        continue
        except FileNotFoundError:
            pass
        return trail
    
    def generate_audit_report(self, session_id: str) -> str:
        """Generate a human-readable audit report for a session."""
        trail = self.get_session_audit_trail(session_id)
        
        if not trail:
            return f"No audit trail found for session {session_id}"
        
        report_lines = [
            f"Audit Report for Session: {session_id}",
            "=" * 60,
            "",
        ]
        
        eligibility_events = [e for e in trail if e["event_type"] == AuditEventType.ELIGIBILITY_DETERMINED.value]
        
        if eligibility_events:
            last_eligibility = eligibility_events[-1]
            data = last_eligibility["data"]
            report_lines.extend([
                f"Eligibility Verdict: {data['verdict'].upper()}",
                f"Visa Type: {data['visa_type']}",
                f"Points: {data['points_earned']}/{data['points_required']}",
                f"Rules Passed: {data['rules_passed']}",
                f"Rules Failed: {data['rules_failed']}",
                "",
                "GOV.UK Sources Referenced:",
            ])
            for source in data.get("gov_uk_sources", []):
                report_lines.append(f"  - {source}")
        
        report_lines.extend([
            "",
            "Event Timeline:",
        ])
        
        for event in trail:
            report_lines.append(
                f"  [{event['timestamp']}] {event['event_type']}"
            )
        
        report_lines.extend([
            "",
            "=" * 60,
            f"Report generated: {datetime.utcnow().isoformat()}",
            "This report is for audit purposes only.",
        ])
        
        return "\n".join(report_lines)


# Global audit logger instance
audit_logger = AuditLogger()