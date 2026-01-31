import logging
from mcp.types import Tool, TextContent
from .adbpg import DatabaseManager

logger = logging.getLogger(__name__)

def get_graphrag_tools() -> list[Tool]:
    """
    返回 ADBPG GraphRAG 工具列表
    """
    return [
        Tool(
            name = "adbpg_graphrag_upload",
            description = "Execute graphrag upload operation",
            # 参数：filename text， context text
            # filename 表示文件名称， context 表示文件内容
            inputSchema = {
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "The file name need to upload"
                    },
                    "context": {
                        "type": "string",
                        "description": "the context of your file"
                    }
                },
                "required": ["filename", "context"]
            }
        ),
        Tool(
            name = "adbpg_graphrag_query",
            description = "Execute graphrag query operation",
            # 参数：query_str text, [query_mode text]
            # query_str 是询问的问题，query_mode 选择查询模式
            inputSchema = {
                "type": "object",
                "properties": {
                    "query_str": {
                        "type": "string",
                        "description": "The query you want to ask"
                    },
                    "query_mode": {
                        "type": "string",
                        "description": "The query mode you need to choose [ bypass,naive, local, global, hybrid, mix[default], tree ]."
                    },
                    "start_search_node_id": {
                        "type": "string",
                        "description": "If using 'tree' query mode, set the start node ID of tree."
                    }
                },
                "required": ["query_str"]
            }
        ),
        Tool(
            name = "adbpg_graphrag_upload_decision_tree",
            description = " Upload a decision tree with the specified root_node. If the root_node does not exist, a new decision tree will be created. ",
            # context text, root_node text
            inputSchema = {
                "type": "object",
                "properties": {
                    "root_node": {
                        "type": "string",
                        "description": "the root_noot (optional)"
                    },
                    "context": {
                        "type": "string",
                        "description": "the context of decision"
                    }
                },
                "required": ["context"]
            }
        ),
        Tool(
            name = "adbpg_graphrag_append_decision_tree",
            description = "Append a subtree to an existing decision tree at the node specified by root_node_id. ",
            # para: context text, root_node_id text
            inputSchema = {
                "type": "object",
                "properties": {
                    "root_node_id": {
                        "type": "string",
                        "description": "the root_noot_id"
                    },
                    "context": {
                        "type": "string",
                        "description": "the context of decision"
                    }
                },
                "required": ["context", "root_node_id"]
            }
        ),
        Tool(
            name = "adbpg_graphrag_delete_decision_tree",
            description = " Delete a sub-decision tree under the node specified by root_node_entity. ",
            # para: root_node_entity text
            inputSchema = {
                "type": "object",
                "properties": {
                    "root_node_entity": {
                        "type": "string",
                        "description": "the root_noot_entity"
                        
                    }
                },
                "required": ["root_node_entity"]
            }
        ),
        Tool(
            name = "adbpg_graphrag_reset_tree_query",
            description = " Reset the decision tree in the tree query mode",
            # para: 
            inputSchema = {
                "type": "object",
                "required": []
            }
        ),
    ]

def _execute_graphrag_tool(sql: str, params: list, db: DatabaseManager) -> list[TextContent]:
    """
    执行 ADBPG GraphRAG 工具并返回结果
    """
    try:
        conn = db.get_graphrag_connection()
        with conn.cursor() as cursor:
            cursor.execute(sql, params)
            if cursor.description:
                json_result = cursor.fetchone()[0]
                return [TextContent(type="text", text=json_result)]
            else:
                return [TextContent(type="text", text="ADBPG GraphRAG Tool executed successfully")]
    except Exception as e:
        logger.error(f"Error executing ADBPG GraphRAG Tool: {e}")
        return [TextContent(type="text", text="Error executing ADBPG GraphRAG Tool")]
    
async def call_graphrag_tool(name: str, arguments: dict, db: DatabaseManager) -> list[TextContent]:
    """
    调用 ADBPG GraphRAG 工具
    """
    if name == "adbpg_graphrag_upload":
        filename, context = arguments.get("filename"), arguments.get("context")
        if not all([filename, context]):
            raise ValueError("Filename and context are required.")
        sql = "SELECT adbpg_graphrag.upload(%s::text, %s::text)"
        params = [filename, context]
    
    elif name == "adbpg_graphrag_query":
        query_str = arguments.get("query_str")
        if not query_str:
            raise ValueError("Query string is required.")
        query_mode = arguments.get("query_mode", "mix")
        start_node = arguments.get("start_search_node_id")

        if start_node:
            sql = "SELECT adbpg_graphrag.query(%s::text, %s::text, %s::text)"
            params = [query_str, query_mode, start_node]
        else:
            sql = "SELECT adbpg_graphrag.query(%s::text, %s::text)"
            params = [query_str, query_mode]
    
    elif name == "adbpg_graphrag_reset_tree_query":
        sql = "SELECT adbpg_graphrag.reset_tree_query()"
        params = []
    
    elif name == "adbpg_graphrag_upload_decision_tree":
        root_node = arguments.get("root_node")
        context = arguments.get("context")
        if not context:
            raise ValueError("Decision Tree Context is required")
        if not root_node:
            root_node = None
        sql = "SELECT adbpg_graphrag.upload_decision_tree(%s::text, %s::text)"
        params = [context, root_node]
    
    elif name == "adbpg_graphrag_append_decision_tree":
        root_node = arguments.get("root_node_id")
        context = arguments.get("context")
        if not context:
            raise ValueError("Decision Tree Context is required")
        if not root_node:
            raise ValueError("Root node id is required")
        sql = "SELECT adbpg_graphrag.append_decision_tree(%s::text, %s::text)"
        params = [context, root_node]

    elif name == "adbpg_graphrag_delete_decision_tree":
        root_node = arguments.get("root_node_entity")
        if not root_node:
            raise ValueError("Root node entity is required")
        sql = "SELECT adbpg_graphrag.delete_decision_tree(%s::text)"
        params = [root_node]

    else:
        raise ValueError(f"Unknown graphrag tool: {name}")
    
    return _execute_graphrag_tool(sql, params, db)