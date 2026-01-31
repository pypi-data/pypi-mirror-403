import json
import logging
from mcp.types import Tool, TextContent
from .adbpg import DatabaseManager

logger = logging.getLogger(__name__)

def get_memory_tools() -> list[Tool]:
    return [
        Tool(
            name = "adbpg_llm_memory_add",
            description = "Execute llm_memory add operation",
            # 参数：messages json, user_id text, run_id text, agent_id text, metadata json
            # 增加新的记忆
            inputSchema={
                "type": "object",
                "properties": {
                    "messages": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "role": {"type": "string"},
                                "content": {"type": "string"}
                            },
                            "required": ["role", "content"]
                        },
                        "description": "List of messages objects (e.g., conversation history)"
                    },
                    "user_id": {
                        "type": "string",
                        "description": "the user_id"
                    },
                    "run_id": {
                        "type": "string",
                        "description": "the run_id"
                    },
                    "agent_id": {
                        "type": "string",
                        "description": "the agent_id"
                    },
                    "metadata": {
                        "type": "object",
                        "description": "the metatdata json"
                    },
                    "memory_type": {
                        "type": "string",
                        "description": "the memory_type text"
                    },
                    "prompt": {
                        "type": "string",
                        "description": "the prompt"
                    }
                },
                "required": ["messages"]
            }
        ),
        Tool(
            name = "adbpg_llm_memory_get_all",
            description = "Execute llm_memory get_all operation",
            # 参数：user_id text, run_id text, agent_id text
            # 获取某个用户或者某个agent的所有记忆
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "The user_id"
                    },
                    "run_id": {
                        "type": "string",
                        "description": "The run_id"
                    },
                    "agent_id": {
                        "type": "string",
                        "description": "The agent_id"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name = "adbpg_llm_memory_search",
            description = "Execute llm_memory search operation",
            # 参数：query text, user_id text, run_id text, agent_id text, filter json
            # 获取与给定 query 相关的记忆
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "llm_memory relevant query"
                    },
                    "user_id": {
                        "type": "string",
                        "description": "The search of user_id"
                    },
                    "run_id": {
                        "type": "string",
                        "description": "The search of run_id"
                    },
                    "agent_id": {
                        "type": "string",
                        "description": "The search of agent_id"
                    },
                    "filter": {
                        "type": "object",
                        "description": "The search of filter"
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name = "adbpg_llm_memory_delete_all",
            description = "Execute llm_memory delete_all operation",
            # 参数：user_id text, run_id text, agent_id text
            # 删除某个用户或者agent的所有记忆
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "The user_id"
                    },
                    "run_id": {
                        "type": "string",
                        "description": "The run_id"
                    },
                    "agent_id": {
                        "type": "string",
                        "description": "The agent_id"
                    }
                },
                "required": []
            }
        )
    ]

def _execute_memory_tool(sql: str, params: list, db: DatabaseManager) -> list[TextContent]:
    try:
        conn = db.get_llm_memory_connection()
        with conn.cursor() as cursor:
            cursor.execute(sql, params)
            if cursor.description:
                json_result = cursor.fetchone()[0]
                return [TextContent(type="text", text=json_result)]
            else:
                return [TextContent(type="text", text="LLM memory tool executed successfully.")]
    except Exception as e:
        return [TextContent(type="text", text=f"Error executing LLM memory tool: {str(e)}")]
    

async def call_memory_tool(name: str, arguments: dict, db: DatabaseManager) -> list[TextContent]:
    """调用 LLM Memory 工具"""
    user_id = arguments.get("user_id")
    run_id = arguments.get("run_id")
    agent_id = arguments.get("agent_id")

    if name == "adbpg_llm_memory_add":
        messages = arguments.get("messages")
        if not messages:
            raise ValueError("messages is required")
        if not any([user_id, run_id, agent_id]):
            raise ValueError("At least one of user_id, run_id, or agent_id must be provided.")
        sql = "SELECT adbpg_llm_memory.add(%s::json, %s::text, %s::text, %s::text, %s::json, %s::text, %s::text)"
        params = [
            json.dumps(messages, ensure_ascii=False),
            user_id, run_id, agent_id,
            json.dumps(arguments.get("metadata"),ensure_ascii=False) if arguments.get("metadata") else None,
            arguments.get("memory_type"),
            arguments.get("prompt")
        ]
    
    elif name == "adbpg_llm_memory_search":
        query = arguments.get("query")
        if not query:
            raise ValueError("query is required")
        if not any([user_id, run_id, agent_id]):
            raise ValueError("At least one of user_id, run_id, or agent_id must be provided.")
        sql = "SELECT adbpg_llm_memory.search(%s::text, %s::text, %s::text, %s::text, %s::json)"
        params = [
            query, user_id, run_id, agent_id,
            json.dumps(arguments.get("filter"), ensure_ascii=False) if arguments.get("filter") else None
        ]
    
    elif name == "adbpg_llm_memory_get_all":
        if not any([user_id, run_id, agent_id]):
            raise ValueError("At least one of user_id, run_id, or agent_id must be provided.")
        sql = "SELECT adbpg_llm_memory.get_all(%s::text, %s::text, %s::text)"
        params = [user_id, run_id, agent_id]
    
    elif name == "adbpg_llm_memory_delete_all":
        if not any([user_id, run_id, agent_id]):
            raise ValueError("At least one of user_id, run_id, or agent_id must be provided.")
        sql = "SELECT adbpg_llm_memory.delete_all(%s::text, %s::text, %s::text)"
        params = [user_id, run_id, agent_id]
    else:
        raise ValueError(f"Unknown memory tool: {name}")
    
    return _execute_memory_tool(sql, params, db)