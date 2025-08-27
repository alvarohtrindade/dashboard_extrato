import pandas as pd
from typing import Optional, Tuple, Any
from config.settings import DatabaseConfig
from utils.logging_utils import Log
from utils.mysql_connector_utils import MySQLConnector

logger = Log.get_logger(__name__)

class DatabaseManager:
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.connector = MySQLConnector(
            host=config.host,
            user=config.user,
            password=config.password,
            database=config.database,
            port=config.port,
            pool_size=config.pool_size,
            pool_timeout=config.pool_timeout
        )
        logger.info("DatabaseManager inicializado com MySQLConnector padronizado")
    
    
    def is_connected(self) -> bool:
        """Verifica se há conexão disponível"""
        return self.connector.test_connection()
    
    def execute_query(self, query: str, params: Optional[Tuple] = None) -> pd.DataFrame:
        """Executa query e retorna DataFrame usando connector padronizado"""
        return self.connector.execute_query_df(query, params)
    
    def execute_update(self, query: str, params: Optional[Tuple] = None) -> int:
        """Executa query de atualização usando connector padronizado"""
        return self.connector.execute_update(query, params)
    
    def close(self):
        """Fecha conexões usando connector padronizado"""
        self.connector.close()