#!/usr/bin/env python3
"""
WowBits CLI - Agent Command

Handles agent management including creating agents from YAML configuration files.
"""

import sys
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

import yaml

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pylibs.database_manager import get_db_manager, get_session_context
from db.schema import (
    Agent,
    AgentSkill,
    AgentStatus,
    MCPConfig,
    PythonFunction,
    Skill,
    SkillSkill,
    SkillTool,
    Tool,
    ToolType,
    ExecMode,
    SequentialAgentExecOrder,
    SequentialSkillExecOrder,
)

DEFAULT_MODEL = "gpt-4.1"

# Agent code template - embedded to avoid file path issues when installed as a package
AGENT_CODE_TEMPLATE = '''from uuid import UUID
import logging
from google.adk.agents import LlmAgent, SequentialAgent, ParallelAgent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StreamableHTTPConnectionParams, SseConnectionParams
from pylibs.database_manager import get_db_manager
from db.schema import (
    Agent, AgentSkill, Skill, SkillSkill, SkillTool, Tool, 
    PythonFunction, MCPConfig, ToolType, ExecMode,
    SequentialAgentExecOrder, SequentialSkillExecOrder
)
from google.adk.models.lite_llm import LiteLlm
from google.genai import types

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

agent_id = "{agent_id}"


def load_python_function(session, python_function_id):
    """Load and execute Python function code from database."""
    pf = session.get(PythonFunction, python_function_id)
    if not pf:
        logger.warning(f"Python function {{python_function_id}} not found")
        return None
    ns = {{}}
    try:
        exec(pf.code, ns)
    except SyntaxError as e:
        logger.exception(f"Syntax error in tool {{pf.name}} at line {{e.lineno}}: {{e.text}}")
        raise
    return ns.get(pf.name)


def load_tools_for_skill(session, skill_id):
    """Load all tools (Python functions and MCP servers) for a skill."""
    tools = []
    links = session.query(SkillTool).filter(SkillTool.skill_id == skill_id).all()
    for link in links:
        tool_ob = session.get(Tool, link.tool_id)
        if not tool_ob:
            continue
        
        if tool_ob.type == ToolType.PYTHON_FUNCTION:
            try:
                fn = load_python_function(session, tool_ob.python_function_id)
                if fn:
                    tools.append(fn)
            except Exception:
                logger.exception(f"Failed loading python function tool for skill {{skill_id}}")
        elif tool_ob.type == ToolType.MCP_SERVER:
            try:
                cfg = session.get(MCPConfig, tool_ob.mcp_config_id)
                if not cfg:
                    continue
                c = cfg.config or {{}}
                transport_mode = c.get("transport_mode")
                if not transport_mode:
                    continue
                if transport_mode == "http":
                    url = cfg.url
                    tools.append(MCPToolset(connection_params=StreamableHTTPConnectionParams(url=url)))
                elif transport_mode == "sse":
                    url = cfg.url
                    tools.append(MCPToolset(connection_params=SseConnectionParams(url=url)))
                else:
                    logger.warning(f"Unknown transport mode: {{transport_mode}}")
                    continue
            except Exception:
                logger.exception(f"Failed loading MCP tool for skill {{skill_id}}")
    return tools


def _build_safety_settings(raw):
    """Convert stored JSON into google.genai.types.SafetySetting objects."""
    if not raw:
        return []
    out = []
    for item in raw:
        try:
            cat = item.get("category")
            thr = item.get("threshold")
            category_enum = (
                getattr(types.HarmCategory, cat)
                if isinstance(cat, str) and hasattr(types.HarmCategory, cat)
                else None
            )
            threshold_enum = (
                getattr(types.HarmBlockThreshold, thr)
                if isinstance(thr, str) and hasattr(types.HarmBlockThreshold, thr)
                else None
            )
            if category_enum and threshold_enum:
                out.append(
                    types.SafetySetting(category=category_enum, threshold=threshold_enum)
                )
        except Exception:
            continue
    return out


def _build_generate_content_config(obj):
    """Build GenerateContentConfig from agent/skill configuration."""
    conf_json = (
        (obj.default_model_config or {{}}) if hasattr(obj, "default_model_config") else {{}}
    )
    temp = (
        obj.temperature
        if getattr(obj, "temperature", None) is not None
        else conf_json.get("temperature", 0.2)
    )
    max_tokens = (
        obj.max_output_tokens
        if getattr(obj, "max_output_tokens", None)
        else conf_json.get("max_output_tokens", 32000)
    )
    raw_safety = (
        obj.safety_settings
        if getattr(obj, "safety_settings", None)
        else conf_json.get("safety_settings", [])
    )
    safety_objects = _build_safety_settings(raw_safety)
    return types.GenerateContentConfig(
        temperature=temp,
        max_output_tokens=max_tokens,
        safety_settings=safety_objects
    )


def build_skill_agent(session, skill, skill_cache, visiting_set):
    """
    Recursively build a skill agent based on its exec_mode.
    Returns an LlmAgent, SequentialAgent, or ParallelAgent.
    """
    if skill.id in skill_cache:
        logger.info(f"Reusing cached skill: {{skill.name}}")
        return skill_cache[skill.id]
    
    if skill.id in visiting_set:
        cycle_path = " -> ".join([str(sid) for sid in visiting_set]) + f" -> {{skill.id}}"
        error_msg = f"Cycle detected in skill hierarchy: {{cycle_path}}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    
    visiting_set.add(skill.id)
    logger.info(f"Building skill: {{skill.name}} (exec_mode={{skill.exec_mode.value}})")
    
    try:
        tools = load_tools_for_skill(session, skill.id)
        child_skills = []
        
        if skill.exec_mode == ExecMode.SEQUENTIAL:
            orders = (
                session.query(SequentialSkillExecOrder)
                .filter(SequentialSkillExecOrder.parent_skill_id == skill.id)
                .order_by(SequentialSkillExecOrder.sequence_num)
                .all()
            )
            for order in orders:
                child_skill = session.get(Skill, order.child_skill_id)
                if child_skill:
                    child_agent = build_skill_agent(session, child_skill, skill_cache, visiting_set)
                    child_skills.append(child_agent)
        
        elif skill.exec_mode == ExecMode.PARALLEL:
            skill_relations = (
                session.query(SkillSkill)
                .filter(SkillSkill.parent_skill_id == skill.id)
                .all()
            )
            for relation in skill_relations:
                child_skill = session.get(Skill, relation.child_skill_id)
                if child_skill:
                    child_agent = build_skill_agent(session, child_skill, skill_cache, visiting_set)
                    child_skills.append(child_agent)
        
        else:
            skill_relations = (
                session.query(SkillSkill)
                .filter(SkillSkill.parent_skill_id == skill.id)
                .all()
            )
            for relation in skill_relations:
                child_skill = session.get(Skill, relation.child_skill_id)
                if child_skill:
                    child_agent = build_skill_agent(session, child_skill, skill_cache, visiting_set)
                    child_skills.append(child_agent)
        
        if skill.exec_mode == ExecMode.SEQUENTIAL and child_skills:
            agent = SequentialAgent(
                name=skill.name,
                sub_agents=child_skills,
                description=skill.description or "",
            )
        elif skill.exec_mode == ExecMode.PARALLEL and child_skills:
            agent = ParallelAgent(
                name=skill.name,
                sub_agents=child_skills,
                description=skill.description or "",
            )
        else:
            llm_kwargs = {{
                "name": skill.name,
                "model": LiteLlm(model=skill.default_model),
                "description": skill.description or "",
                "instruction": skill.instructions or "",
                "tools": tools,
                "generate_content_config": _build_generate_content_config(skill)
            }}
            if child_skills:
                llm_kwargs["sub_agents"] = child_skills
            if skill.output_key:
                llm_kwargs["output_key"] = skill.output_key
            agent = LlmAgent(**llm_kwargs)
        
        skill_cache[skill.id] = agent
        logger.info(f"Built skill agent: {{skill.name}} (type={{type(agent).__name__}})")
        return agent
    
    finally:
        visiting_set.discard(skill.id)


def create_agent():
    """Create hierarchical agent from database with support for sequential/parallel execution."""
    session = get_db_manager().get_session()
    try:
        agent = session.get(Agent, UUID(agent_id))
        if not agent:
            raise RuntimeError(f"Agent not found: {{agent_id}}")
        
        logger.info(f"Creating agent: {{agent.name}} (exec_mode={{agent.exec_mode.value}})")
        
        skill_cache = {{}}
        visiting_set = set()
        child_agents = []
        
        if agent.exec_mode == ExecMode.SEQUENTIAL:
            orders = (
                session.query(SequentialAgentExecOrder)
                .filter(SequentialAgentExecOrder.agent_id == agent.id)
                .order_by(SequentialAgentExecOrder.sequence_num)
                .all()
            )
            for order in orders:
                skill = session.get(Skill, order.skill_id)
                if skill:
                    skill_agent = build_skill_agent(session, skill, skill_cache, visiting_set)
                    child_agents.append(skill_agent)
        
        elif agent.exec_mode == ExecMode.PARALLEL:
            links = session.query(AgentSkill).filter(AgentSkill.agent_id == agent.id).all()
            for link in links:
                skill = session.get(Skill, link.skill_id)
                if skill:
                    skill_agent = build_skill_agent(session, skill, skill_cache, visiting_set)
                    child_agents.append(skill_agent)
        
        else:
            links = session.query(AgentSkill).filter(AgentSkill.agent_id == agent.id).all()
            for link in links:
                skill = session.get(Skill, link.skill_id)
                if skill:
                    skill_agent = build_skill_agent(session, skill, skill_cache, visiting_set)
                    child_agents.append(skill_agent)
        
        if agent.exec_mode == ExecMode.SEQUENTIAL:
            root = SequentialAgent(
                name=agent.name,
                sub_agents=child_agents,
                description=agent.description or "",
            )
        elif agent.exec_mode == ExecMode.PARALLEL:
            root = ParallelAgent(
                name=agent.name,
                sub_agents=child_agents,
                description=agent.description or "",
            )
        else:
            llm_kwargs = {{
                "name": agent.name,
                "model": LiteLlm(model=agent.default_model),
                "description": agent.description or "",
                "instruction": agent.instructions or "",
                "generate_content_config": _build_generate_content_config(agent)
            }}
            if child_agents:
                llm_kwargs["sub_agents"] = child_agents
            if agent.output_key:
                llm_kwargs["output_key"] = agent.output_key
            root = LlmAgent(**llm_kwargs)
        
        logger.info(f"Successfully created root agent: {{agent.name}} (type={{type(root).__name__}})")
        logger.info(f"Total unique skills in hierarchy: {{len(skill_cache)}}")
        return root
    
    except RuntimeError as e:
        logger.error(f"Failed to create agent due to cycle: {{e}}")
        raise
    except Exception as e:
        logger.exception(f"Error creating agent: {{e}}")
        raise
    finally:
        session.close()


root_agent = create_agent()
'''


# =============================================================================
# YAML Parsing & Validation
# =============================================================================

def parse_exec_mode(mode_str: str) -> ExecMode:
    """Parse execution mode from string to enum."""
    if not mode_str:
        return ExecMode.LLM
    mode_key = str(mode_str).upper()
    try:
        return ExecMode[mode_key]
    except KeyError:
        valid = ", ".join([member.name for member in ExecMode])
        raise ValueError(f"Unknown exec_mode '{mode_str}'. Valid options: {valid}")


def load_yaml_config(config_path: Path) -> Dict[str, Any]:
    """Parse YAML configuration file into tools, skills and agents."""
    with config_path.open("r", encoding="utf-8") as handle:
        docs = [doc for doc in yaml.safe_load_all(handle) if doc]

    if not docs:
        raise ValueError(f"No YAML documents found in {config_path}")

    tools: Dict[str, Dict[str, Any]] = {}
    skills: Dict[str, Dict[str, Any]] = {}
    agents: List[Dict[str, Any]] = []

    for idx, doc in enumerate(docs, start=1):
        if not isinstance(doc, dict):
            raise ValueError(f"Document #{idx} is not a mapping: {doc}")

        kind = str(doc.get("kind", "")).strip().lower()
        if not kind:
            raise ValueError(f"Document #{idx} is missing 'kind'")

        name = doc.get("name")
        if not name:
            raise ValueError(f"Document #{idx} ({kind}) is missing 'name'")

        config = doc.get("config", {}) or {}

        if kind == "tool":
            # Parse tool definition
            tool_type = doc.get("type", "PYTHON_FUNCTION")
            tool_entry = {
                "description": doc.get("description", ""),
                "type": tool_type,
            }
            
            # Add type-specific fields
            if tool_type.upper() == "PYTHON_FUNCTION":
                tool_entry["python_function_name"] = doc.get("python_function_name", name)
            elif tool_type.upper() == "MCP_SERVER":
                tool_entry["mcp_config_name"] = doc.get("mcp_config_name")
                tool_entry["url"] = doc.get("url")
                tool_entry["mcp_config"] = doc.get("mcp_config", {})
            
            tools[name] = tool_entry

        elif kind == "skill":
            exec_mode_str = config.get("exec_mode", "llm")
            exec_mode = parse_exec_mode(exec_mode_str)

            skills[name] = {
                "description": doc.get("description", ""),
                "instructions": doc.get("instructions", ""),
                "default_model": config.get("default_model")
                or config.get("model")
                or DEFAULT_MODEL,
                "default_model_config": config.get("default_model_config")
                or config.get("model_config")
                or {},
                "temperature": config.get("temperature", 0.2),
                "max_output_tokens": config.get("max_output_tokens", 32000),
                "safety_settings": config.get("safety_settings", []),
                "exec_mode": exec_mode,
                "output_key": config.get("output_key"),
                "tools": doc.get("tools", []) or [],
                "skills": doc.get("skills", []) or [],
            }

        elif kind == "agent":
            exec_mode_str = config.get("exec_mode", "llm")
            exec_mode = parse_exec_mode(exec_mode_str)

            agents.append(
                {
                    "name": name,
                    "description": doc.get("description", ""),
                    "instructions": doc.get("instructions", ""),
                    "status": doc.get("status", "ACTIVE"),
                    "default_model": config.get("default_model")
                    or config.get("model")
                    or DEFAULT_MODEL,
                    "default_model_config": config.get("default_model_config")
                    or config.get("model_config")
                    or {},
                    "temperature": config.get("temperature", 0.2),
                    "max_output_tokens": config.get("max_output_tokens", 32000),
                    "safety_settings": config.get("safety_settings", []),
                    "exec_mode": exec_mode,
                    "output_key": config.get("output_key"),
                    "skills": doc.get("skills", []) or [],
                }
            )
        else:
            raise ValueError(
                f"Unsupported kind '{doc.get('kind')}' in document #{idx}; "
                "only 'tool', 'skill' and 'agent' are supported."
            )

    if not agents:
        raise ValueError("At least one 'agent' document is required in the YAML file.")

    return {"tools": tools, "skills": skills, "agents": agents}


# =============================================================================
# Tool Management
# =============================================================================

def get_or_create_tool(session, tool_name: str, tool_def: Dict[str, Any]) -> Tool:
    """
    Create or update a Tool from YAML definition.

    Args:
        session: Database session
        tool_name: Name of the tool
        tool_def: Tool definition from YAML with keys:
            - type: PYTHON_FUNCTION, MCP_SERVER, API, DATABASE
            - description: Tool description
            - python_function_name: name to lookup in python_functions table
            - mcp_config_name: name to lookup in mcp_configs table

    Returns:
        Tool: The created or updated tool

    Raises:
        ValueError: If referenced python_function or mcp_config not found in DB
    """
    print(f"  🔧 Processing tool '{tool_name}'...")
    
    # Parse tool type
    type_str = str(tool_def.get("type")).upper()
    try:
        tool_type = ToolType[type_str]
    except KeyError:
        valid = ", ".join([m.name for m in ToolType])
        raise ValueError(f"Unknown tool type '{type_str}'. Valid: {valid}")

    description = tool_def.get("description") or f"{tool_name} tool"
    
    # Get foreign key IDs based on tool type
    python_function_id = None
    mcp_config_id = None
    
    if tool_type == ToolType.PYTHON_FUNCTION:
        function_name = tool_def.get("python_function_name") or tool_name
        python_function = (
            session.query(PythonFunction)
            .filter(PythonFunction.name == function_name)
            .first()
        )
        if not python_function:
            raise ValueError(
                f"❌ Python function '{function_name}' not found in database.\n"
                f"   Run 'wowbits sync functions' to populate python_functions table first."
            )
        python_function_id = python_function.id
        print(f"    ├─ 📝 Found python_function '{function_name}' (id={python_function_id})")
        
    elif tool_type == ToolType.MCP_SERVER:
        mcp_name = tool_def.get("mcp_config_name") or tool_name
        mcp_config = (
            session.query(MCPConfig)
            .filter(MCPConfig.name == mcp_name)
            .first()
        )
        if not mcp_config:
            raise ValueError(
                f"❌ MCP config '{mcp_name}' not found in database.\n"
                f"   Create the MCP config first using 'wowbits create mcp'."
            )
        mcp_config_id = mcp_config.id
        print(f"    ├─ 🔌 Found mcp_config '{mcp_name}' (id={mcp_config_id})")
    
    # Check if tool already exists
    tool = session.query(Tool).filter(Tool.name == tool_name).first()
    
    if not tool:
        # Create new tool
        tool = Tool(
            id=uuid4(),
            name=tool_name,
            description=description,
            type=tool_type,
            python_function_id=python_function_id,
            mcp_config_id=mcp_config_id,
        )
        session.add(tool)
        session.flush()
        print(f"    └─ ✅ Created tool '{tool_name}' (id={tool.id}, type={type_str})")
    else:
        # Update existing tool
        print(f"    ├─ ℹ️  Tool '{tool_name}' already exists (id={tool.id}), updating...")
        updated_fields = []
        
        if tool.description != description:
            tool.description = description
            updated_fields.append("description")
        if tool.type != tool_type:
            tool.type = tool_type
            updated_fields.append("type")
        if tool.python_function_id != python_function_id:
            tool.python_function_id = python_function_id
            updated_fields.append("python_function_id")
        if tool.mcp_config_id != mcp_config_id:
            tool.mcp_config_id = mcp_config_id
            updated_fields.append("mcp_config_id")
        
        if updated_fields:
            session.flush()
            print(f"    └─ ✅ Updated tool '{tool_name}' (fields: {', '.join(updated_fields)})")
        else:
            print(f"    └─ ℹ️  Tool '{tool_name}' unchanged")
    
    return tool


# =============================================================================
# Skill Management
# =============================================================================

def get_or_create_skill(
    session,
    skill_name: str,
    skill_config: Dict[str, Any],
    all_skills: Dict[str, Dict[str, Any]],
    skill_registry: Dict[str, Skill],
    all_tools: Dict[str, Dict[str, Any]] = None,
    depth: int = 0,
    visiting_path: List[str] = None,
) -> Skill:
    """
    Recursively upsert a skill and its child skills with PER-PATH cycle detection.

    Relationship Storage Strategy:
    - ALL child relationships → skill_skills table (always)
    - SEQUENTIAL mode only → ALSO add to sequential_skill_exec_order (for ordering)

    This means:
    - skill_skills contains ALL parent-child relationships
    - sequential_skill_exec_order contains ONLY sequential relationships with order info

    Args:
        session: Database session
        skill_name: Name of the skill to process
        skill_config: Configuration dict for this skill from YAML
        all_skills: Complete dict of all skills from YAML
        skill_registry: Cache of already-built skills (allows DAG reuse)
        depth: Current recursion depth (for logging)
        visiting_path: List of skill names in current path (detects cycles)

    Returns:
        Skill object (created or retrieved from cache)

    Raises:
        ValueError: If a cycle is detected in the skill hierarchy
    """
    if visiting_path is None:
        visiting_path = []

    indent = "  " * depth

    # 🔥 CYCLE DETECTION: Check if skill appears in CURRENT PATH
    if skill_name in visiting_path:
        cycle = " -> ".join(visiting_path) + f" -> {skill_name}"
        raise ValueError(
            f"❌ Cycle detected in skill hierarchy:\n"
            f"   Path: {cycle}\n"
            f"   Skills cannot reference their ancestors."
        )

    # ✅ Check cache (allows skill reuse in different branches)
    if skill_name in skill_registry:
        print(f"{indent}♻️  Skill '{skill_name}' already processed (reusing)")
        return skill_registry[skill_name]

    print(
        f"{indent}📦 Processing skill '{skill_name}' "
        f"[exec_mode={skill_config.get('exec_mode', ExecMode.LLM).value}]"
    )

    skill = session.query(Skill).filter(Skill.name == skill_name).first()

    standard_fields = {
        "description": skill_config.get("description", ""),
        "instructions": skill_config.get("instructions", ""),
        "default_model": skill_config.get("default_model", DEFAULT_MODEL),
        "default_model_config": skill_config.get("default_model_config", {}),
        "temperature": skill_config.get("temperature", 0.2),
        "max_output_tokens": skill_config.get("max_output_tokens", 32000),
        "safety_settings": skill_config.get("safety_settings", []),
        "exec_mode": skill_config.get("exec_mode", ExecMode.LLM),
        "output_key": skill_config.get("output_key"),
    }

    if not skill:
        skill = Skill(id=uuid4(), name=skill_name, **standard_fields)
        session.add(skill)
        session.flush()
        print(f"{indent}  ✅ Created skill '{skill_name}' ({skill.id})")
    else:
        updated = False
        for field, value in standard_fields.items():
            if getattr(skill, field) != value:
                setattr(skill, field, value)
                updated = True
        if updated:
            session.flush()
            print(f"{indent}  ✅ Updated skill '{skill_name}' ({skill.id})")
        else:
            print(f"{indent}  ℹ️  Skill '{skill_name}' unchanged")

    skill_registry[skill_name] = skill

    # ========================================
    # TOOL ASSOCIATIONS
    # ========================================
    deleted_tools = (
        session.query(SkillTool)
        .filter(SkillTool.skill_id == skill.id)
        .delete(synchronize_session=False)
    )

    if deleted_tools > 0:
        print(f"{indent}  🗑️  Cleared {deleted_tools} old tool associations")

    tools = skill_config.get("tools", []) or []
    if all_tools is None:
        all_tools = {}
    
    if tools:
        print(f"{indent}  🔧 Linking {len(tools)} tools...")
        
    for tool_name in tools:
        # Check if tool is defined in YAML (kind: tool)
        tool_def = all_tools.get(tool_name)
        
        if tool_def:
            # Tool is defined in YAML, create/update it
            tool = get_or_create_tool(session, tool_name, tool_def)
        else:
            # Tool not defined in YAML, check if it exists in DB
            tool = session.query(Tool).filter(Tool.name == tool_name).first()
            if not tool:
                raise ValueError(
                    f"❌ Tool '{tool_name}' referenced by skill '{skill_name}' not found.\n"
                    f"   Either define it in the YAML file (kind: tool) or ensure it exists in the database."
                )
            print(f"{indent}    ├─ 🔧 Found existing tool '{tool_name}' in DB")
        
        session.add(SkillTool(skill_id=skill.id, tool_id=tool.id))
        print(f"{indent}    └─ ✅ Linked tool '{tool_name}' to skill '{skill_name}'")

    # ========================================
    # CHILD SKILL RELATIONSHIPS (with cycle detection)
    # ========================================
    child_skill_names = skill_config.get("skills", []) or []

    if child_skill_names:
        exec_mode = skill_config.get("exec_mode", ExecMode.LLM)
        print(f"{indent}  🌳 Processing {len(child_skill_names)} child skills...")

        # 🔥 ALWAYS clear BOTH tables (handles exec_mode changes)
        deleted_sequential = (
            session.query(SequentialSkillExecOrder)
            .filter(SequentialSkillExecOrder.parent_skill_id == skill.id)
            .delete(synchronize_session=False)
        )

        deleted_skill_skill = (
            session.query(SkillSkill)
            .filter(SkillSkill.parent_skill_id == skill.id)
            .delete(synchronize_session=False)
        )

        if deleted_sequential > 0 or deleted_skill_skill > 0:
            print(
                f"{indent}  🗑️  Cleared {deleted_sequential} sequential + "
                f"{deleted_skill_skill} skill_skill relationships"
            )

        # 🔥 Add current skill to path before processing children
        visiting_path.append(skill_name)

        try:
            # Process each child skill
            for idx, child_skill_name in enumerate(child_skill_names, start=1):
                if child_skill_name not in all_skills:
                    print(
                        f"{indent}    ⚠️  Warning: Child skill '{child_skill_name}' not defined in YAML"
                    )
                    continue

                # 🔥 Pass visiting_path.copy() to detect cycles in THIS path
                # (copy allows different branches to reuse skills)
                child_skill = get_or_create_skill(
                    session,
                    child_skill_name,
                    all_skills[child_skill_name],
                    all_skills,
                    skill_registry,
                    all_tools,
                    depth + 1,
                    visiting_path.copy(),  # Pass copy to allow branching
                )

                # 🔑 KEY CHANGE: ALWAYS create skill_skills entry for ALL exec_modes
                skill_skill = SkillSkill(
                    id=uuid4(), parent_skill_id=skill.id, child_skill_id=child_skill.id
                )
                session.add(skill_skill)

                # 🔑 For SEQUENTIAL mode, ALSO add ordering information
                if exec_mode == ExecMode.SEQUENTIAL:
                    seq_order = SequentialSkillExecOrder(
                        id=uuid4(),
                        parent_skill_id=skill.id,
                        child_skill_id=child_skill.id,
                        sequence_num=idx,
                    )
                    session.add(seq_order)
                    print(
                        f"{indent}    ├─ ⏭️  Sequential #{idx}: '{child_skill_name}' "
                        f"(stored in skill_skills + sequential_skill_exec_order)"
                    )
                elif exec_mode == ExecMode.PARALLEL:
                    print(
                        f"{indent}    ├─ ⚡ Parallel: '{child_skill_name}' "
                        f"(stored in skill_skills only)"
                    )
                else:  # LLM
                    print(
                        f"{indent}    ├─ 🤖 LLM sub-skill: '{child_skill_name}' "
                        f"(stored in skill_skills only)"
                    )

        finally:
            # 🔥 IMPORTANT: Remove current skill from path after processing
            # (backtracking for DFS)
            visiting_path.pop()

    session.flush()
    return skill


# =============================================================================
# Agent Management
# =============================================================================

def coerce_agent_status(status_value: Any) -> AgentStatus:
    """Convert status value to AgentStatus enum."""
    if isinstance(status_value, AgentStatus):
        return status_value
    if not status_value:
        return AgentStatus.ACTIVE
    status_key = str(status_value).upper()
    try:
        return AgentStatus[status_key]
    except KeyError as exc:
        valid = ", ".join([member.name for member in AgentStatus])
        raise ValueError(
            f"Unknown agent status '{status_value}'. Valid options: {valid}"
        ) from exc


def upsert_agent(
    session, agent_config: Dict[str, Any], skill_registry: Dict[str, Skill]
) -> Agent:
    """
    Create or update an agent and its skill associations.

    Relationship Storage Strategy:
    - ALL skill relationships → agent_skills table (always)
    - SEQUENTIAL mode only → ALSO add to sequential_agent_exec_order (for ordering)
    """
    agent_name = agent_config["name"]
    print(
        f"\n🎯 Processing agent '{agent_name}' "
        f"[exec_mode={agent_config.get('exec_mode', ExecMode.LLM).value}]"
    )

    agent = session.query(Agent).filter(Agent.name == agent_name).first()

    standard_fields = {
        "description": agent_config.get("description", ""),
        "instructions": agent_config.get("instructions", ""),
        "status": coerce_agent_status(agent_config.get("status")),
        "default_model": agent_config.get("default_model", DEFAULT_MODEL),
        "default_model_config": agent_config.get("default_model_config", {}),
        "temperature": agent_config.get("temperature", 0.2),
        "max_output_tokens": agent_config.get("max_output_tokens", 32000),
        "safety_settings": agent_config.get("safety_settings", []),
        "exec_mode": agent_config.get("exec_mode", ExecMode.LLM),
        "output_key": agent_config.get("output_key"),
    }

    if not agent:
        agent = Agent(id=uuid4(), name=agent_name, **standard_fields)
        session.add(agent)
        session.flush()
        print(f"  ✅ Created agent '{agent_name}' ({agent.id})")
    else:
        updated = False
        for field, value in standard_fields.items():
            if getattr(agent, field) != value:
                setattr(agent, field, value)
                updated = True
        if updated:
            session.flush()
            print(f"  ✅ Updated agent '{agent_name}' ({agent.id})")
        else:
            print(f"  ℹ️  Agent '{agent_name}' unchanged")

    # ========================================
    # SKILL ASSOCIATIONS
    # ========================================
    # 🔥 ALWAYS clear BOTH tables
    deleted_agent_skills = (
        session.query(AgentSkill)
        .filter(AgentSkill.agent_id == agent.id)
        .delete(synchronize_session=False)
    )

    deleted_sequential = (
        session.query(SequentialAgentExecOrder)
        .filter(SequentialAgentExecOrder.agent_id == agent.id)
        .delete(synchronize_session=False)
    )

    if deleted_agent_skills > 0 or deleted_sequential > 0:
        print(
            f"  🗑️  Cleared {deleted_agent_skills} agent_skill + "
            f"{deleted_sequential} sequential_order relationships"
        )

    exec_mode = agent_config.get("exec_mode", ExecMode.LLM)
    skill_names = agent_config.get("skills", [])
    print(f"  🔗 Linking {len(skill_names)} skills...")

    for idx, skill_name in enumerate(skill_names, start=1):
        # First check skill_registry (skills defined in current YAML)
        skill = skill_registry.get(skill_name)
        
        if not skill:
            # Check if skill exists in database
            skill = session.query(Skill).filter(Skill.name == skill_name).first()
        
        if not skill:
            raise ValueError(
                f"❌ Skill '{skill_name}' referenced by agent '{agent_name}' not found.\n"
                f"   Either define it in the YAML file (kind: skill) or ensure it exists in the database."
            )

        # 🔑 ALWAYS create AgentSkill link for ALL exec_modes
        session.add(AgentSkill(agent_id=agent.id, skill_id=skill.id))

        # 🔑 For SEQUENTIAL mode, ALSO add ordering information
        if exec_mode == ExecMode.SEQUENTIAL:
            seq_order = SequentialAgentExecOrder(
                id=uuid4(), agent_id=agent.id, skill_id=skill.id, sequence_num=idx
            )
            session.add(seq_order)
            print(
                f"    ├─ ⏭️  Sequential #{idx}: '{skill_name}' "
                f"(stored in agent_skills + sequential_agent_exec_order)"
            )
        elif exec_mode == ExecMode.PARALLEL:
            print(
                f"    ├─ ⚡ Parallel: '{skill_name}' " f"(stored in agent_skills only)"
            )
        else:  # LLM
            print(f"    ├─ 🤖 LLM: '{skill_name}' " f"(stored in agent_skills only)")

    session.flush()
    return agent




# =============================================================================
# CLI Functions
# =============================================================================

def get_agent_studio_dir() -> Optional[Path]:
    """
    Get the agent_studio directory from WOWBITS_ROOT_DIR environment variable.
    
    Returns:
        Path to the agent_studio directory or None if not set
    """
    root_dir = os.environ.get("WOWBITS_ROOT_DIR")
    
    if not root_dir:
        # Try to load from .env file
        try:
            from dotenv import load_dotenv
            load_dotenv()
            root_dir = os.environ.get("WOWBITS_ROOT_DIR")
        except ImportError:
            pass
    
    if not root_dir:
        print("❌ Error: WOWBITS_ROOT_DIR environment variable is not set.")
        print("   Please run 'wowbits setup' first or set the environment variable.")
        return None
    
    return Path(root_dir) / "agent_studio"


def create_agent(agent_name: str, config_path: Optional[str] = None) -> Tuple[List[str], List[str]]:
    """
    Create an agent from a YAML configuration file.
    
    The YAML file should contain tool, skill, and agent definitions separated by '---'.
    Processing order: tools → skills → agents
    
    Args:
        agent_name: Name of the agent to create
        config_path: Optional custom path to the YAML config file.
                     If not provided, looks for WOWBITS_ROOT_DIR/agent_studio/<agent_name>.yaml
    
    Returns:
        Tuple of (created_skills, affected_agents)
    """
    print("\n╔═══════════════════════════════════════════════════════════════╗")
    print("║               Create Agent from YAML                          ║")
    print("╚═══════════════════════════════════════════════════════════════╝\n")
    
    # Determine the config file path
    if config_path:
        yaml_path = Path(config_path).expanduser().resolve()
    else:
        # Use default path: WOWBITS_ROOT_DIR/agent_studio/<agent_name>.yaml
        agent_studio_dir = get_agent_studio_dir()
        if not agent_studio_dir:
            sys.exit(1)
        yaml_path = agent_studio_dir / f"{agent_name}.yaml"
    
    # Validate the file exists
    if not yaml_path.exists():
        print(f"❌ Error: Configuration file not found: {yaml_path}")
        if not config_path:
            print(f"\n   Expected location: WOWBITS_ROOT_DIR/agent_studio/{agent_name}.yaml")
            print("   You can also specify a custom path with -c <path>")
        sys.exit(1)
    
    print(f"📄 Loading agent configuration from: {yaml_path}\n")
    
    # Parse YAML config
    try:
        config = load_yaml_config(yaml_path)
    except ValueError as e:
        print(f"❌ YAML parsing error: {e}")
        sys.exit(1)
    
    # Get database session
    db_manager = get_db_manager()
    session = db_manager.get_session()
    
    created_tools: List[str] = []
    created_skills: List[str] = []
    affected_agents: List[str] = []
    
    try:
        # =============================================
        # PHASE 1: Process Tools
        # =============================================
        all_tools = config.get("tools", {})
        if all_tools:
            print(f"🔧 PHASE 1: Processing {len(all_tools)} tools...")
            print("-" * 60)
            
            for tool_name, tool_def in all_tools.items():
                tool = get_or_create_tool(session, tool_name, tool_def)
                created_tools.append(tool.name)
            
            print()
        
        # =============================================
        # PHASE 2: Process Skills
        # =============================================
        all_skills = config.get("skills", {})
        skill_registry: Dict[str, Skill] = {}
        
        if all_skills:
            print(f"📚 PHASE 2: Processing {len(all_skills)} skills...")
            print("-" * 60)
            
            for skill_name, skill_config in all_skills.items():
                if skill_name not in skill_registry:
                    skill = get_or_create_skill(
                        session=session,
                        skill_name=skill_name,
                        skill_config=skill_config,
                        all_skills=all_skills,
                        skill_registry=skill_registry,
                        all_tools=all_tools,
                        depth=0,
                        visiting_path=[],
                    )
                    created_skills.append(skill.name)
            
            print()
        
        # =============================================
        # PHASE 3: Process Agents
        # =============================================
        agents_config = config.get("agents", [])
        if agents_config:
            print(f"🎯 PHASE 3: Processing {len(agents_config)} agents...")
            print("-" * 60)
            
            for agent_config in agents_config:
                agent = upsert_agent(session, agent_config, skill_registry)
                affected_agents.append(agent.name)
        
        # Commit all changes
        session.commit()
        
        # Print summary
        print("\n" + "=" * 60)
        print("✅ Agent creation completed successfully!")
        print("=" * 60)
        print(f"📊 Summary:")
        print(f"   • Tools processed: {len(created_tools)}")
        print(f"   • Skills processed: {len(created_skills)}")
        print(f"   • Agents processed: {len(affected_agents)}")
        print("=" * 60 + "\n")
        
        return created_skills, affected_agents
        
    except ValueError as e:
        session.rollback()
        print(f"\n❌ Validation Error: {e}")
        print("   All changes have been rolled back.")
        sys.exit(1)
    except Exception as e:
        session.rollback()
        print(f"\n❌ Error during agent creation: {e}")
        print("   All changes have been rolled back.")
        raise
    finally:
        session.close()
    


def list_agents() -> None:
    """List all agents in the database."""
    print("\n╔═══════════════════════════════════════════════════════════════╗")
    print("║               Agents                                          ║")
    print("╚═══════════════════════════════════════════════════════════════╝\n")
    
    try:
        with get_session_context() as session:
            agents = session.query(Agent).all()
            
            if not agents:
                print("  ℹ️  No agents found in database")
                return
            
            print(f"Found {len(agents)} agent(s):\n")
            print(f"{'Name':<30} {'Status':<12} {'Exec Mode':<12} {'Description':<30}")
            print("-" * 84)
            
            for agent in agents:
                name = agent.name[:28] + ".." if len(agent.name) > 30 else agent.name
                status = agent.status.value if agent.status else "-"
                exec_mode = agent.exec_mode.value if agent.exec_mode else "-"
                desc = (agent.description or "")[:28] + ".." if len(agent.description or "") > 30 else (agent.description or "-")
                print(f"{name:<30} {status:<12} {exec_mode:<12} {desc:<30}")
            
            print()
            
    except Exception as e:
        print(f"\n❌ Error listing agents: {e}")
        raise


def get_agent_runner_dir() -> Optional[Path]:
    """
    Get the agent_runner directory from WOWBITS_ROOT_DIR environment variable.
    
    Returns:
        Path to the agent_runner directory or None if not set
    """
    root_dir = os.environ.get("WOWBITS_ROOT_DIR")
    
    if not root_dir:
        # Try to load from .env file
        try:
            from dotenv import load_dotenv
            load_dotenv()
            root_dir = os.environ.get("WOWBITS_ROOT_DIR")
        except ImportError:
            pass
    
    if not root_dir:
        print("❌ Error: WOWBITS_ROOT_DIR environment variable is not set.")
        print("   Please run 'wowbits setup' first or set the environment variable.")
        return None
    
    return Path(root_dir) / "agent_runner"


def create_agent_code(agent_id: str, agent_name: str, agent_runner_path: Path) -> Path:
    """
    Create the agent.py file for an agent in the agent_runner directory.
    
    Args:
        agent_id: UUID of the agent
        agent_name: Name of the agent
        agent_runner_path: Path to the agent_runner directory
        
    Returns:
        Path to the created agent folder
    """
    # Sanitize folder name
    safe_folder_name = _sanitize_folder_name(agent_name)
    agent_folder = agent_runner_path / safe_folder_name
    
    # Create agent folder
    agent_folder.mkdir(parents=True, exist_ok=True)
    
    # Generate agent.py from template
    agent_code = AGENT_CODE_TEMPLATE.format(agent_id=agent_id)
    
    # Write agent.py file
    agent_file_path = agent_folder / "agent.py"
    with open(agent_file_path, "w") as f:
        f.write(agent_code)
    
    print(f"✅ Generated agent code: {agent_file_path}")
    return agent_folder


def run_agent(agent_name: str, exec_mode: str = "web") -> None:
    """
    Run an agent in the specified execution mode.
    
    Args:
        agent_name: Name of the agent to run
        exec_mode: Execution mode - 'web' or 'api'
    """
    print(f"\n🚀 Running agent '{agent_name}' in {exec_mode} mode...\n")
    
    if exec_mode not in ["web", "api"]:
        print(f"❌ Invalid exec_mode '{exec_mode}'. Must be 'web' or 'api'")
        sys.exit(1)
    
    try:
        # Get agent_runner directory from WOWBITS_ROOT_DIR
        agent_runner_path = get_agent_runner_dir()
        if not agent_runner_path:
            sys.exit(1)
        
        # Create agent_runner directory if it doesn't exist
        agent_runner_path.mkdir(parents=True, exist_ok=True)
        
        with get_session_context() as session:
            # Verify agent exists
            agent = session.query(Agent).filter(Agent.name == agent_name).first()
            
            if not agent:
                print(f"❌ Agent '{agent_name}' not found in database")
                print("   Run 'wowbits list agents' to see available agents")
                sys.exit(1)
            
            print(f"✅ Found agent '{agent_name}' (ID: {agent.id})")
            
            # Create agent code in agent_runner directory
            agent_folder = create_agent_code(str(agent.id), agent.name, agent_runner_path)
        
        if exec_mode == "web":
            print(f"\n🌐 Starting ADK web server...")
            print(f"   Working directory: {agent_runner_path}")
            
            # Change to agent_runner directory and run adk web command
            import subprocess
            result = subprocess.run(
                ["adk", "web"],
                cwd=str(agent_runner_path),
                check=False
            )
            
            if result.returncode != 0:
                print(f"\n❌ ADK web command failed with exit code {result.returncode}")
                sys.exit(result.returncode)
        
        elif exec_mode == "api":
            print(f"\n🔌 API mode not yet implemented")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

def _sanitize_folder_name(name: str) -> str:
    """Convert agent name to safe filesystem folder name."""
    import re
    safe_name = re.sub(r"[^\w\s-]", "", name)
    safe_name = re.sub(r"[-\s]+", "_", safe_name)
    safe_name = safe_name.lower().strip("_")
    return safe_name if safe_name else "unnamed_agent"


if __name__ == "__main__":
    # For testing purposes
    import argparse
    
    parser = argparse.ArgumentParser(description="Manage agents")
    subparsers = parser.add_subparsers(dest="action", help="Action to perform")
    
    # create subcommand
    create_parser = subparsers.add_parser("create", help="Create an agent from YAML")
    create_parser.add_argument("name", help="Agent name")
    create_parser.add_argument("-c", "--config", help="Custom path to YAML config file")
    
    # list subcommand
    subparsers.add_parser("list", help="List all agents")
    
    args = parser.parse_args()
    
    if args.action == "create":
        create_agent(args.name, args.config)
    elif args.action == "list":
        list_agents()
    else:
        parser.print_help()
