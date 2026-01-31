# mcp_server/db.py
import psycopg
import logging
import json
from psycopg import Connection
from .adbpg_config import AppConfig
from typing import Optional, Callable
from .adbpg_config import settings

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, config: AppConfig):
        self._config_info = config.get_db_connection_info()
        self._conn = None
        self._graphrag_conn = None
        self._llm_memory_conn = None
        self.db_master_port = self.get_master_port()

    def _get_connection(self, conn_attr: str, initializer: Optional[Callable[[Connection],None]] = None) -> Connection:
        """通用连接获取和健康检查逻辑"""

        def _create_and_initialize() -> Connection:
            new_conn = psycopg.connect(**self._config_info)
            new_conn.autocommit = True

            if initializer:
                logger.info(f"Running initializer for {conn_attr} on new connection...")
                try:
                    initializer(new_conn)
                except Exception as e:
                    logger.error(f"Error initializing {conn_attr}: {e}")
                    new_conn.close()
                    raise e
            setattr(self, conn_attr, new_conn)
            return new_conn
        
        conn = getattr(self, conn_attr)
        
        if conn is None or conn.closed:
            logger.info(f"Connecting to database for {conn_attr}...")
            conn = _create_and_initialize()
            logger.info(f"New database connection established and initialized for {conn_attr} (id: {id(conn)})")
        else:
            try:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1;")
            except psycopg.Error:
                logger.warning(f"Connection for {conn_attr} is stale. Reconnecting...")
                conn.close()
                conn = psycopg.connect(**self._config_info)
                conn.autocommit = True
                setattr(self, conn_attr, conn)
                logger.info(f"Reconnected for {conn_attr} (id: {id(conn)})")
        return conn

    def get_basic_connection(self) -> Connection:
        """获取用于基本操作的连接"""
        return self._get_connection('_conn')

    def get_graphrag_connection(self) -> Connection:
        """
        获取 GraphRAG 专用的长连接
        每次重新获得连接就初始化
        """
        def initializer(conn: Connection):
            try:
                config_json = json.dumps(settings.get_graphrag_init_config())
                with conn.cursor() as cursor:
                    cursor.execute("SELECT adbpg_graphrag.initialize(%s::json);", (config_json,))
            except Exception as e:
                logger.error(f"ADBPG GraphRAG initialization failed: {e}")
                raise RuntimeError(f"ADBPG GraphRAG initialization failed: {e}") from e
        return self._get_connection('_graphrag_conn', initializer=initializer)

    def get_llm_memory_connection(self) -> Connection:
        """
        获取 LLM Memory 专用的长连接
        每次重新连接就初始化
        """
        def initializer(conn: Connection):
            try:
                config_json = json.dumps(settings.get_memory_init_config(self.db_master_port))
                with conn.cursor() as cursor:
                    cursor.execute("SELECT adbpg_llm_memory.config(%s::json);", (config_json,))
            except Exception as e:
                logger.error(f"ADBPG LLM Memory initialization failed: {e}")
                raise RuntimeError(f"ADBPG LLM Memory initialization failed: {e}") from e

        return self._get_connection('_llm_memory_conn',initializer=initializer)

    def get_master_port(self) -> int:
        """获取 master 节点的端口，用于 llm_memory 配置"""
        sql = "SELECT port FROM gp_segment_configuration WHERE content = -1 AND role = 'p';"
        try:
            with self.get_basic_connection().cursor() as cursor:
                cursor.execute(sql)
                port = cursor.fetchone()[0]
                return port
        except psycopg.Error as e:
            logger.error(f"Database error while getting master port: {e}")
            raise RuntimeError(f"Database error: {str(e)}") from e

    def close_all(self):
        """关闭所有连接"""
        if self._conn and not self._conn.closed:
            self._conn.close()
        if self._graphrag_conn and not self._graphrag_conn.closed:
            self._graphrag_conn.close()
        if self._llm_memory_conn and not self._llm_memory_conn.closed:
            self._llm_memory_conn.close()
        logger.info("All database connections closed.")

