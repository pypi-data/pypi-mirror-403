# src/db/schema.py
import uuid
import enum
from sqlalchemy import (
    Column, String, Text, ForeignKey, Enum as SQLAlchemyEnum, JSON, Boolean
)
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from sqlalchemy import DateTime
from sqlalchemy import Index, Integer, Float  # added Float
from dotenv import load_dotenv
load_dotenv()

Base = declarative_base()

# --- ENUM Definitions ---
class AgentStatus(enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    MAINTENANCE = "MAINTENANCE"

class ToolType(enum.Enum):
    API = "API"
    DATABASE = "DATABASE"
    PYTHON_FUNCTION = "PYTHON_FUNCTION"
    MCP_SERVER = "MCP_SERVER"

class CodeStorageType(enum.Enum):
    database = "database"
    mcp_server = "mcp_server"
    local = "local"

class ExecMode(enum.Enum):
    LLM = "llm"
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"

class ConnectorStatus(enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


# --- Model Definitions ---
class User(Base):
    __tablename__ = 'users'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    first_name = Column(String(255), nullable=False)
    last_name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    chat_sessions = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")
    chat_messages = relationship("ChatMessage", back_populates="user", cascade="all, delete-orphan")


class Agent(Base):
    """Maps to the 'agents' table."""
    __tablename__ = 'agents'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text)
    instructions = Column(Text, nullable=False)
    status = Column(SQLAlchemyEnum(AgentStatus), default=AgentStatus.ACTIVE)
    default_model = Column(String(255), nullable=False)
    default_model_config = Column(JSON, default=dict)
    temperature = Column(Float, nullable=True, default=0.2)
    max_output_tokens = Column(Integer, nullable=True, default=32000)
    safety_settings = Column(JSON, nullable=True, default=list)
    exec_mode = Column(SQLAlchemyEnum(ExecMode), default=ExecMode.LLM)
    output_key = Column(String(255), nullable=True)


    agent_skills = relationship("AgentSkill", back_populates="agent", cascade="all, delete-orphan")
    chat_sessions = relationship("ChatSession", back_populates="agent", cascade="all, delete-orphan")
    chat_messages = relationship("ChatMessage", back_populates="agent", cascade="all, delete-orphan")

    sequential_agent_exec_orders = relationship(
        "SequentialAgentExecOrder", 
        back_populates="agent", 
        cascade="all, delete-orphan"
    )


class Skill(Base):
    """Maps to the 'skills' table."""
    __tablename__ = 'skills'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text)
    instructions = Column(Text, nullable=False)
    default_model = Column(String(255), nullable=False)
    default_model_config = Column(JSON, default=dict)
    temperature = Column(Float, nullable=True, default=0.2)
    max_output_tokens = Column(Integer, nullable=True, default=32000)
    safety_settings = Column(JSON, nullable=True, default=list)
    exec_mode = Column(SQLAlchemyEnum(ExecMode), default=ExecMode.LLM)
    output_key = Column(String(255), nullable=True)


    agent_skills = relationship("AgentSkill", back_populates="skill", cascade="all, delete-orphan")
    skill_tools = relationship("SkillTool", back_populates="skill", cascade="all, delete-orphan")
    chat_messages = relationship("ChatMessage", back_populates="skill", cascade="all, delete-orphan")

    parent_skill_relations = relationship(
        "SkillSkill", 
        foreign_keys="SkillSkill.parent_skill_id", 
        back_populates="parent_skill", 
        cascade="all, delete-orphan"
    )
    child_skill_relations = relationship(
        "SkillSkill", 
        foreign_keys="SkillSkill.child_skill_id", 
        back_populates="child_skill", 
        cascade="all, delete-orphan"
    )
    sequential_skill_exec_orders_as_parent = relationship(
        "SequentialSkillExecOrder", 
        foreign_keys="SequentialSkillExecOrder.parent_skill_id", 
        back_populates="parent_skill", 
        cascade="all, delete-orphan"
    )
    sequential_skill_exec_orders_as_child = relationship(
        "SequentialSkillExecOrder", 
        foreign_keys="SequentialSkillExecOrder.child_skill_id", 
        back_populates="child_skill", 
        cascade="all, delete-orphan"
    )


class AgentSkill(Base):
    __tablename__ = 'agent_skills'
    agent_id = Column(UUID(as_uuid=True), ForeignKey('agents.id', ondelete="CASCADE"), primary_key=True)
    skill_id = Column(UUID(as_uuid=True), ForeignKey('skills.id', ondelete="CASCADE"), primary_key=True)

    agent = relationship("Agent", back_populates="agent_skills")
    skill = relationship("Skill", back_populates="agent_skills")

class SkillSkill(Base):
    __tablename__ = 'skill_skills'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    parent_skill_id = Column(UUID(as_uuid=True), ForeignKey('skills.id', ondelete="CASCADE"), nullable=False)
    child_skill_id = Column(UUID(as_uuid=True), ForeignKey('skills.id', ondelete="CASCADE"), nullable=False)

    parent_skill = relationship("Skill", foreign_keys=[parent_skill_id], back_populates="parent_skill_relations")
    child_skill = relationship("Skill", foreign_keys=[child_skill_id], back_populates="child_skill_relations")


class SequentialSkillExecOrder(Base):
    __tablename__ = 'sequential_skill_exec_order'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    parent_skill_id = Column(UUID(as_uuid=True), ForeignKey('skills.id', ondelete="CASCADE"), nullable=False)
    child_skill_id = Column(UUID(as_uuid=True), ForeignKey('skills.id', ondelete="CASCADE"), nullable=False)
    sequence_num = Column(Integer, nullable=False)

    parent_skill = relationship("Skill", foreign_keys=[parent_skill_id], back_populates="sequential_skill_exec_orders_as_parent")
    child_skill = relationship("Skill", foreign_keys=[child_skill_id], back_populates="sequential_skill_exec_orders_as_child")


class SequentialAgentExecOrder(Base):
    __tablename__ = 'sequential_agent_exec_order'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(UUID(as_uuid=True), ForeignKey('agents.id', ondelete="CASCADE"), nullable=False)
    skill_id = Column(UUID(as_uuid=True), ForeignKey('skills.id', ondelete="CASCADE"), nullable=False)
    sequence_num = Column(Integer, nullable=False)

    agent = relationship("Agent", back_populates="sequential_agent_exec_orders")
    skill = relationship("Skill")


class SkillTool(Base):
    __tablename__ = 'skill_tools'
    skill_id = Column(UUID(as_uuid=True), ForeignKey('skills.id', ondelete="CASCADE"), primary_key=True)
    tool_id = Column(UUID(as_uuid=True), ForeignKey('tools.id', ondelete="CASCADE"), primary_key=True)

    skill = relationship("Skill", back_populates="skill_tools")
    tool = relationship("Tool", back_populates="skill_tools")


class MCPConfig(Base):
    __tablename__ = 'mcp_configs'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, unique=True)
    url = Column(Text)
    config = Column(JSON)


class Connector(Base):
    """
    Connectors table - stores external service integrations.
    Each connector represents a connection to an external service (e.g., FIRECRAWL, FMP, SERP).
    """
    __tablename__ = 'connectors'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, unique=True)
    provider = Column(String(255), nullable=False)  # e.g., 'slack', 'discord', 'notion', 'airtable'
    config = Column(JSON, default=dict)  # Provider-specific configuration (API keys, tokens, etc.)
    status = Column(SQLAlchemyEnum(ConnectorStatus), default=ConnectorStatus.ACTIVE)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PythonFunction(Base):
    __tablename__ = 'python_functions'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text)
    code = Column(Text)


class Tool(Base):
    __tablename__ = 'tools'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text)
    type = Column(SQLAlchemyEnum(ToolType), nullable=False)
    python_function_id = Column(UUID(as_uuid=True), ForeignKey('python_functions.id'), nullable=True)
    mcp_config_id = Column(UUID(as_uuid=True), ForeignKey('mcp_configs.id'), nullable=True)

    python_function = relationship("PythonFunction")
    mcp_config = relationship("MCPConfig")
    skill_tools = relationship("SkillTool", back_populates="tool", cascade="all, delete-orphan")
    chat_messages = relationship("ChatMessage", back_populates="tool", cascade="all, delete-orphan")


class ChatSession(Base):
    __tablename__ = 'chat_sessions'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(UUID(as_uuid=True), ForeignKey('agents.id'), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    title = Column(String(500))
    summary = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    agent = relationship("Agent", back_populates="chat_sessions")
    user = relationship("User", back_populates="chat_sessions")
    chat_messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")


class ChatMessage(Base):
    __tablename__ = 'chat_messages'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey('chat_sessions.id'), nullable=False)
    agent_id = Column(UUID(as_uuid=True), ForeignKey('agents.id'))
    skill_id = Column(UUID(as_uuid=True), ForeignKey('skills.id'))
    tool_id = Column(UUID(as_uuid=True), ForeignKey('tools.id'))
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    session = relationship("ChatSession", back_populates="chat_messages")
    agent = relationship("Agent", back_populates="chat_messages")
    skill = relationship("Skill", back_populates="chat_messages")
    tool = relationship("Tool", back_populates="chat_messages")
    user = relationship("User", back_populates="chat_messages")


if __name__ == "__main__":
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    import sys
    import os

    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    sys.path.insert(0, parent_dir)

    try:
        from pylibs.env_loader import load_env_variables
        load_env_variables()
        db_url = os.getenv('WOWBITS_DB_CONNECTION_STRING')
        print(f"Database connection string: {db_url}")
        engine = create_engine(db_url)
        Session = sessionmaker(bind=engine)
        session = Session()
        Base.metadata.create_all(engine)
        print("Database tables created successfully!")
        session.close()
    except ImportError as e:
        print(f"Import error: {e}")
        print("Make sure you're running this from the src directory")
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure WOWBITS_DB_CONNECTION_STRING is set in your environment")
