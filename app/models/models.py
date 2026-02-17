import uuid
from datetime import datetime, date
from enum import Enum as PyEnum

from sqlalchemy import (
    Column, String, Float, DateTime, Date, ForeignKey, Text, Enum, Boolean, Index
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


# --- Enums ---

class PlanTier(str, PyEnum):
    FREE = "free"
    PRO = "pro"
    TEAM = "team"
    CUSTOM = "custom"


class AccountStatus(str, PyEnum):
    PENDING = "pending"
    ACTIVE = "active"
    ERROR = "error"
    DISCONNECTED = "disconnected"


class AlertChannel(str, PyEnum):
    EMAIL = "email"
    SLACK = "slack"


class AnomalySeverity(str, PyEnum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class ResourceType(str, PyEnum):
    EC2_INSTANCE = "ec2_instance"
    EBS_VOLUME = "ebs_volume"
    EBS_SNAPSHOT = "ebs_snapshot"
    RDS_INSTANCE = "rds_instance"
    ELASTIC_IP = "elastic_ip"
    LOAD_BALANCER = "load_balancer"
    LAMBDA_FUNCTION = "lambda_function"


class BudgetPeriod(str, PyEnum):
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"


# --- Models ---

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    plan = Column(Enum(PlanTier), default=PlanTier.FREE, nullable=False)
    stripe_customer_id = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    aws_accounts = relationship("AWSAccount", back_populates="user", cascade="all, delete-orphan")
    alert_configs = relationship("AlertConfig", back_populates="user", cascade="all, delete-orphan")


class AWSAccount(Base):
    __tablename__ = "aws_accounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    aws_account_id = Column(String(12), nullable=False)
    role_arn = Column(String(255), nullable=False)
    external_id = Column(String(255), nullable=False)
    account_name = Column(String(255), nullable=True)
    status = Column(Enum(AccountStatus), default=AccountStatus.PENDING, nullable=False)
    last_sync_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="aws_accounts")
    cost_records = relationship("CostRecord", back_populates="aws_account", cascade="all, delete-orphan")
    anomalies = relationship("Anomaly", back_populates="aws_account", cascade="all, delete-orphan")
    recommendations = relationship("Recommendation", back_populates="aws_account", cascade="all, delete-orphan")
    budgets = relationship("Budget", back_populates="aws_account", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_aws_accounts_user_id", "user_id"),
    )


class CostRecord(Base):
    __tablename__ = "cost_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    aws_account_id = Column(UUID(as_uuid=True), ForeignKey("aws_accounts.id"), nullable=False)
    date = Column(Date, nullable=False)
    service = Column(String(255), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="USD", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    aws_account = relationship("AWSAccount", back_populates="cost_records")

    __table_args__ = (
        Index("ix_cost_records_account_date", "aws_account_id", "date"),
        Index("ix_cost_records_date_service", "date", "service"),
    )


class Anomaly(Base):
    __tablename__ = "anomalies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    aws_account_id = Column(UUID(as_uuid=True), ForeignKey("aws_accounts.id"), nullable=False)
    date = Column(Date, nullable=False)
    service = Column(String(255), nullable=False)
    expected_amount = Column(Float, nullable=False)
    actual_amount = Column(Float, nullable=False)
    deviation_pct = Column(Float, nullable=False)  # e.g., 0.45 means 45% above expected
    severity = Column(Enum(AnomalySeverity), nullable=False)
    acknowledged = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    aws_account = relationship("AWSAccount", back_populates="anomalies")

    __table_args__ = (
        Index("ix_anomalies_account_date", "aws_account_id", "date"),
    )


class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    aws_account_id = Column(UUID(as_uuid=True), ForeignKey("aws_accounts.id"), nullable=False)
    resource_type = Column(Enum(ResourceType), nullable=False)
    resource_id = Column(String(255), nullable=False)  # e.g., i-0abc123, vol-0xyz456
    region = Column(String(50), nullable=False)
    recommendation = Column(Text, nullable=False)
    estimated_monthly_savings = Column(Float, nullable=False)
    is_resolved = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    aws_account = relationship("AWSAccount", back_populates="recommendations")

    __table_args__ = (
        Index("ix_recommendations_account", "aws_account_id"),
    )


class Budget(Base):
    __tablename__ = "budgets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    aws_account_id = Column(UUID(as_uuid=True), ForeignKey("aws_accounts.id"), nullable=False)
    name = Column(String(255), nullable=False)
    amount = Column(Float, nullable=False)  # budget limit in USD
    period = Column(Enum(BudgetPeriod), default=BudgetPeriod.MONTHLY, nullable=False)
    service_filter = Column(String(255), nullable=True)  # null = all services
    alert_at_pct = Column(Float, default=0.80, nullable=False)  # alert at 80%
    is_active = Column(Boolean, default=True, nullable=False)
    current_spend = Column(Float, default=0.0, nullable=False)  # cached current spend
    last_checked_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    aws_account = relationship("AWSAccount", back_populates="budgets")

    __table_args__ = (
        Index("ix_budgets_account", "aws_account_id"),
    )


class SharedReport(Base):
    __tablename__ = "shared_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    aws_account_id = Column(UUID(as_uuid=True), ForeignKey("aws_accounts.id"), nullable=False)
    token = Column(String(64), unique=True, nullable=False, index=True)
    title = Column(String(255), nullable=False)
    report_data = Column(Text, nullable=False)  # JSON snapshot of the report
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    aws_account = relationship("AWSAccount")


class AlertConfig(Base):
    __tablename__ = "alert_configs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    channel = Column(Enum(AlertChannel), nullable=False)
    is_enabled = Column(Boolean, default=True, nullable=False)

    # Email-specific
    email_address = Column(String(255), nullable=True)

    # Slack-specific
    slack_webhook_url = Column(String(500), nullable=True)

    # Thresholds
    notify_info = Column(Boolean, default=False, nullable=False)
    notify_warning = Column(Boolean, default=True, nullable=False)
    notify_critical = Column(Boolean, default=True, nullable=False)
    daily_summary = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="alert_configs")

    __table_args__ = (
        Index("ix_alert_configs_user_id", "user_id"),
    )
