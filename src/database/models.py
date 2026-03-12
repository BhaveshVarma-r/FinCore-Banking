import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Float, Boolean,
    DateTime, Text, ForeignKey, JSON
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


def new_uuid():
    return str(uuid.uuid4())


class AuditSession(Base):
    __tablename__ = "audit_sessions"

    id = Column(String, primary_key=True, default=new_uuid)
    session_id = Column(String, nullable=False, index=True)
    customer_id = Column(String, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    total_latency_ms = Column(Integer, nullable=True)
    risk_level = Column(String, default="low")
    required_human = Column(Boolean, default=False)
    status = Column(String, default="in_progress")
    agents_invoked = Column(JSON, default=list)
    intents = Column(JSON, default=list)

    queries = relationship("AuditQuery", back_populates="session", cascade="all, delete")
    mcp_calls = relationship("AuditMCPCall", back_populates="session", cascade="all, delete")
    kg_queries = relationship("AuditKGQuery", back_populates="session", cascade="all, delete")
    agent_decisions = relationship("AuditAgentDecision", back_populates="session", cascade="all, delete")
    escalations = relationship("AuditEscalation", back_populates="session", cascade="all, delete")


class AuditQuery(Base):
    __tablename__ = "audit_queries"

    id = Column(String, primary_key=True, default=new_uuid)
    session_id = Column(String, ForeignKey("audit_sessions.session_id"), nullable=False)
    query = Column(Text, nullable=False)
    intents = Column(JSON, default=list)
    agents_invoked = Column(JSON, default=list)
    final_response = Column(Text, nullable=True)
    planner_plan = Column(JSON, nullable=True)
    critique_passed = Column(Boolean, nullable=True)
    critique_feedback = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    timestamp = Column(DateTime, default=datetime.utcnow)

    session = relationship("AuditSession", back_populates="queries")


class AuditMCPCall(Base):
    __tablename__ = "audit_mcp_calls"

    id = Column(String, primary_key=True, default=new_uuid)
    session_id = Column(String, ForeignKey("audit_sessions.session_id"), nullable=False)
    agent_name = Column(String, nullable=False)
    server_name = Column(String, nullable=False)
    tool_name = Column(String, nullable=False)
    input_params = Column(JSON, nullable=True)
    output_result = Column(JSON, nullable=True)
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)
    latency_ms = Column(Integer, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    session = relationship("AuditSession", back_populates="mcp_calls")


class AuditKGQuery(Base):
    __tablename__ = "audit_kg_queries"

    id = Column(String, primary_key=True, default=new_uuid)
    session_id = Column(String, ForeignKey("audit_sessions.session_id"), nullable=False)
    agent_name = Column(String, nullable=False)
    query_name = Column(String, nullable=False)
    params = Column(JSON, nullable=True)
    result_count = Column(Integer, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    session = relationship("AuditSession", back_populates="kg_queries")


class AuditAgentDecision(Base):
    __tablename__ = "audit_agent_decisions"

    id = Column(String, primary_key=True, default=new_uuid)
    session_id = Column(String, ForeignKey("audit_sessions.session_id"), nullable=False)
    agent_name = Column(String, nullable=False)
    decision_type = Column(String, nullable=True)
    input_summary = Column(Text, nullable=True)
    output_summary = Column(Text, nullable=True)
    reasoning = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    session = relationship("AuditSession", back_populates="agent_decisions")


class AuditEscalation(Base):
    __tablename__ = "audit_escalations"

    id = Column(String, primary_key=True, default=new_uuid)
    session_id = Column(String, ForeignKey("audit_sessions.session_id"), nullable=False)
    customer_id = Column(String, nullable=False, index=True)
    risk_level = Column(String, nullable=False)
    reason = Column(Text, nullable=True)
    case_id = Column(String, nullable=True)
    resolved = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    session = relationship("AuditSession", back_populates="escalations")