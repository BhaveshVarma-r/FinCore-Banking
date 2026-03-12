import time
from datetime import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from src.database.database import get_db_session
from src.database.models import (
    AuditSession, AuditQuery, AuditMCPCall,
    AuditKGQuery, AuditAgentDecision, AuditEscalation,
)
import structlog

logger = structlog.get_logger(__name__)


class AuditService:
    """Handles all audit database writes and reads."""

    # ── Write Operations ─────────────────────────────────────────────────

    def create_session(
        self,
        session_id: str,
        customer_id: str,
    ) -> AuditSession:
        db = get_db_session()
        try:
            record = AuditSession(
                session_id=session_id,
                customer_id=customer_id,
                status="in_progress",
            )
            db.add(record)
            db.commit()
            db.refresh(record)
            logger.info("audit.session_created", session_id=session_id)
            return record
        finally:
            db.close()

    def complete_session(
        self,
        session_id: str,
        total_latency_ms: int,
        risk_level: str,
        required_human: bool,
        agents_invoked: List[str],
        intents: List[str],
        status: str = "completed",
    ):
        db = get_db_session()
        try:
            record = db.query(AuditSession).filter_by(session_id=session_id).first()
            if record:
                record.completed_at = datetime.utcnow()
                record.total_latency_ms = total_latency_ms
                record.risk_level = risk_level
                record.required_human = required_human
                record.agents_invoked = agents_invoked
                record.intents = intents
                record.status = status
                db.commit()
                logger.info("audit.session_completed", session_id=session_id)
        finally:
            db.close()

    def log_query(
        self,
        session_id: str,
        query: str,
        intents: List[str],
        agents_invoked: List[str],
        final_response: str,
        planner_plan: Optional[Dict] = None,
        critique_passed: Optional[bool] = None,
        critique_feedback: Optional[str] = None,
        retry_count: int = 0,
    ):
        db = get_db_session()
        try:
            record = AuditQuery(
                session_id=session_id,
                query=query,
                intents=intents,
                agents_invoked=agents_invoked,
                final_response=final_response,
                planner_plan=planner_plan,
                critique_passed=critique_passed,
                critique_feedback=critique_feedback,
                retry_count=retry_count,
            )
            db.add(record)
            db.commit()
        finally:
            db.close()

    def log_mcp_call(
        self,
        session_id: str,
        agent_name: str,
        server_name: str,
        tool_name: str,
        input_params: Dict,
        output_result: Dict,
        success: bool,
        latency_ms: int,
        error_message: Optional[str] = None,
    ):
        db = get_db_session()
        try:
            record = AuditMCPCall(
                session_id=session_id,
                agent_name=agent_name,
                server_name=server_name,
                tool_name=tool_name,
                input_params=input_params,
                output_result=output_result,
                success=success,
                latency_ms=latency_ms,
                error_message=error_message,
            )
            db.add(record)
            db.commit()
        finally:
            db.close()

    def log_kg_query(
        self,
        session_id: str,
        agent_name: str,
        query_name: str,
        params: Dict,
        result_count: int,
    ):
        db = get_db_session()
        try:
            record = AuditKGQuery(
                session_id=session_id,
                agent_name=agent_name,
                query_name=query_name,
                params=params,
                result_count=result_count,
            )
            db.add(record)
            db.commit()
        finally:
            db.close()

    def log_agent_decision(
        self,
        session_id: str,
        agent_name: str,
        decision_type: str,
        input_summary: str,
        output_summary: str,
        reasoning: str,
    ):
        db = get_db_session()
        try:
            record = AuditAgentDecision(
                session_id=session_id,
                agent_name=agent_name,
                decision_type=decision_type,
                input_summary=input_summary,
                output_summary=output_summary,
                reasoning=reasoning,
            )
            db.add(record)
            db.commit()
        finally:
            db.close()

    def log_escalation(
        self,
        session_id: str,
        customer_id: str,
        risk_level: str,
        reason: str,
        case_id: Optional[str] = None,
    ):
        db = get_db_session()
        try:
            record = AuditEscalation(
                session_id=session_id,
                customer_id=customer_id,
                risk_level=risk_level,
                reason=reason,
                case_id=case_id,
            )
            db.add(record)
            db.commit()
            logger.warning("audit.escalation_logged",
                          session_id=session_id,
                          risk_level=risk_level)
        finally:
            db.close()

    # ── Read Operations ──────────────────────────────────────────────────

    def get_session_audit(self, session_id: str) -> Optional[Dict]:
        db = get_db_session()
        try:
            session = db.query(AuditSession).filter_by(session_id=session_id).first()
            if not session:
                return None
            queries = db.query(AuditQuery).filter_by(session_id=session_id).all()
            mcp_calls = db.query(AuditMCPCall).filter_by(session_id=session_id).all()
            kg_queries = db.query(AuditKGQuery).filter_by(session_id=session_id).all()
            decisions = db.query(AuditAgentDecision).filter_by(session_id=session_id).all()
            escalations = db.query(AuditEscalation).filter_by(session_id=session_id).all()

            return {
                "session": {
                    "session_id": session.session_id,
                    "customer_id": session.customer_id,
                    "created_at": str(session.created_at),
                    "completed_at": str(session.completed_at) if session.completed_at else None,
                    "total_latency_ms": session.total_latency_ms,
                    "risk_level": session.risk_level,
                    "required_human": session.required_human,
                    "agents_invoked": session.agents_invoked,
                    "status": session.status,
                },
                "queries": [
                    {
                        "query": q.query,
                        "intents": q.intents,
                        "agents_invoked": q.agents_invoked,
                        "final_response": q.final_response,
                        "planner_plan": q.planner_plan,
                        "critique_passed": q.critique_passed,
                        "critique_feedback": q.critique_feedback,
                        "retry_count": q.retry_count,
                        "timestamp": str(q.timestamp),
                    }
                    for q in queries
                ],
                "mcp_calls": [
                    {
                        "agent": c.agent_name,
                        "server": c.server_name,
                        "tool": c.tool_name,
                        "params": c.input_params,
                        "success": c.success,
                        "latency_ms": c.latency_ms,
                        "error": c.error_message,
                        "timestamp": str(c.timestamp),
                    }
                    for c in mcp_calls
                ],
                "kg_queries": [
                    {
                        "agent": k.agent_name,
                        "query": k.query_name,
                        "params": k.params,
                        "result_count": k.result_count,
                        "timestamp": str(k.timestamp),
                    }
                    for k in kg_queries
                ],
                "agent_decisions": [
                    {
                        "agent": d.agent_name,
                        "type": d.decision_type,
                        "reasoning": d.reasoning,
                        "timestamp": str(d.timestamp),
                    }
                    for d in decisions
                ],
                "escalations": [
                    {
                        "customer_id": e.customer_id,
                        "risk_level": e.risk_level,
                        "reason": e.reason,
                        "case_id": e.case_id,
                        "resolved": e.resolved,
                        "timestamp": str(e.timestamp),
                    }
                    for e in escalations
                ],
            }
        finally:
            db.close()

    def get_customer_audit_history(self, customer_id: str, limit: int = 20) -> List[Dict]:
        db = get_db_session()
        try:
            sessions = (
                db.query(AuditSession)
                .filter_by(customer_id=customer_id)
                .order_by(AuditSession.created_at.desc())
                .limit(limit)
                .all()
            )
            return [
                {
                    "session_id": s.session_id,
                    "created_at": str(s.created_at),
                    "risk_level": s.risk_level,
                    "required_human": s.required_human,
                    "agents_invoked": s.agents_invoked,
                    "total_latency_ms": s.total_latency_ms,
                    "status": s.status,
                }
                for s in sessions
            ]
        finally:
            db.close()

    def get_all_escalations(self, resolved: Optional[bool] = None) -> List[Dict]:
        db = get_db_session()
        try:
            query = db.query(AuditEscalation)
            if resolved is not None:
                query = query.filter_by(resolved=resolved)
            escalations = query.order_by(AuditEscalation.timestamp.desc()).all()
            return [
                {
                    "id": e.id,
                    "session_id": e.session_id,
                    "customer_id": e.customer_id,
                    "risk_level": e.risk_level,
                    "reason": e.reason,
                    "case_id": e.case_id,
                    "resolved": e.resolved,
                    "timestamp": str(e.timestamp),
                }
                for e in escalations
            ]
        finally:
            db.close()

    def get_stats(self) -> Dict:
        db = get_db_session()
        try:
            total_sessions = db.query(AuditSession).count()
            completed = db.query(AuditSession).filter_by(status="completed").count()
            escalated = db.query(AuditSession).filter_by(required_human=True).count()
            total_mcp = db.query(AuditMCPCall).count()
            failed_mcp = db.query(AuditMCPCall).filter_by(success=False).count()
            total_kg = db.query(AuditKGQuery).count()
            return {
                "total_sessions": total_sessions,
                "completed_sessions": completed,
                "escalated_sessions": escalated,
                "total_mcp_calls": total_mcp,
                "failed_mcp_calls": failed_mcp,
                "total_kg_queries": total_kg,
            }
        finally:
            db.close()


audit_service = AuditService()