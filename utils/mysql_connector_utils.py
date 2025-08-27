"""
Módulo MySQL padronizado conforme CLAUDE.md
Pool de conexões thread-safe com retry e logging robusto
"""
import os
import time
import threading
from typing import Any, Dict, List, Optional, Tuple, Union
import mysql.connector
from mysql.connector import pooling
import pandas as pd
from contextlib import contextmanager

from .logging_utils import Log

logger = Log.get_logger(__name__)

class MySQLConnector:
    _instance = None
    _lock = threading.Lock()
    _pool = None
    
    def __init__(
        self,
        host: str = None,
        user: str = None, 
        password: str = None,
        database: str = None,
        port: int = 3306,
        pool_size: int = 10,
        pool_timeout: int = 30,
        max_retries: int = 3
    ):
        self.config = {
            'host': host or os.getenv('DB_HOST', 'localhost'),
            'user': user or os.getenv('DB_USER', 'root'),
            'password': password or os.getenv('DB_PASSWORD', ''),
            'database': database or os.getenv('DB_NAME', 'DW_STAGING'),
            'port': port or int(os.getenv('DB_PORT', 3306)),
            'pool_size': pool_size or int(os.getenv('DB_POOL_SIZE', 10)),
            'pool_timeout': pool_timeout or int(os.getenv('DB_POOL_TIMEOUT', 30)),
            'charset': 'utf8mb4',
            'collation': 'utf8mb4_unicode_ci',
            'autocommit': True,
            'connect_timeout': 10,
            'buffered': True
        }
        self.max_retries = max_retries
        self._initialize_pool()
    
    def _initialize_pool(self):
        """Inicializa pool de conexões com retry"""
        with MySQLConnector._lock:
            if MySQLConnector._pool is not None:
                self.pool = MySQLConnector._pool
                return
            
            retry_delay = 2
            
            for attempt in range(self.max_retries):
                try:
                    logger.info(f"Inicializando pool MySQL - tentativa {attempt + 1}")
                    
                    pool_config = {
                        'pool_name': 'mysql_pool',
                        'pool_size': self.config['pool_size'],
                        'pool_reset_session': True,
                        'host': self.config['host'],
                        'user': self.config['user'],
                        'password': self.config['password'],
                        'database': self.config['database'],
                        'port': self.config['port'],
                        'charset': self.config['charset'],
                        'collation': self.config['collation'],
                        'autocommit': self.config['autocommit'],
                        'connect_timeout': self.config['connect_timeout']
                    }
                    
                    MySQLConnector._pool = mysql.connector.pooling.MySQLConnectionPool(**pool_config)
                    self.pool = MySQLConnector._pool
                    
                    # Teste de conexão
                    test_conn = self.pool.get_connection()
                    test_conn.ping(reconnect=True)
                    test_conn.close()
                    
                    logger.info("Pool MySQL inicializado com sucesso")
                    return
                    
                except Exception as e:
                    logger.error(f"Erro na tentativa {attempt + 1}: {str(e)}")
                    if attempt < self.max_retries - 1:
                        time.sleep(retry_delay)
                        retry_delay *= 2
                    else:
                        logger.critical("Falha ao inicializar pool MySQL")
                        raise
    
    @contextmanager
    def get_connection(self):
        """Context manager para conexões"""
        connection = None
        try:
            connection = self.pool.get_connection()
            connection.ping(reconnect=True)
            yield connection
        except Exception as e:
            logger.error(f"Erro na conexão: {str(e)}")
            if connection:
                connection.rollback()
            raise
        finally:
            if connection and connection.is_connected():
                connection.close()
    
    def execute_query(self, query: str, params: Optional[Tuple] = None) -> List[Dict[str, Any]]:
        """Executa query e retorna lista de dicts"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(dictionary=True, buffered=True)
                
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                results = cursor.fetchall()
                cursor.close()
                
                logger.debug(f"Query executada: {len(results)} resultados")
                return results
                
        except Exception as e:
            logger.error(f"Erro ao executar query: {str(e)}")
            logger.debug(f"Query: {query}")
            logger.debug(f"Params: {params}")
            raise
    
    def execute_query_df(self, query: str, params: Optional[Tuple] = None) -> pd.DataFrame:
        """Executa query e retorna DataFrame pandas"""
        try:
            with self.get_connection() as conn:
                if params:
                    df = pd.read_sql(query, conn, params=params)
                else:
                    df = pd.read_sql(query, conn)
                
                logger.debug(f"Query executada: {len(df)} registros no DataFrame")
                return df
                
        except Exception as e:
            logger.error(f"Erro ao executar query_df: {str(e)}")
            logger.debug(f"Query: {query}")
            logger.debug(f"Params: {params}")
            return pd.DataFrame()
    
    def execute_update(self, query: str, params: Optional[Tuple] = None) -> int:
        """Executa query de atualização/inserção"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(buffered=True)
                
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                affected_rows = cursor.rowcount
                conn.commit()
                cursor.close()
                
                logger.info(f"Update executado: {affected_rows} linhas afetadas")
                return affected_rows
                
        except Exception as e:
            logger.error(f"Erro ao executar update: {str(e)}")
            logger.debug(f"Query: {query}")
            logger.debug(f"Params: {params}")
            raise
    
    def execute_many(self, query: str, params_list: List[Tuple]) -> int:
        """Executa múltiplas queries com parâmetros diferentes"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(buffered=True)
                cursor.executemany(query, params_list)
                
                affected_rows = cursor.rowcount
                conn.commit()
                cursor.close()
                
                logger.info(f"ExecuteMany: {len(params_list)} operações, {affected_rows} linhas afetadas")
                return affected_rows
                
        except Exception as e:
            logger.error(f"Erro ao executar executemany: {str(e)}")
            raise
    
    def query_single_value(self, query: str, params: Optional[Tuple] = None) -> Any:
        """Executa query e retorna um único valor"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(buffered=True)
                
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                result = cursor.fetchone()
                cursor.close()
                
                return result[0] if result else None
                
        except Exception as e:
            logger.error(f"Erro ao executar query_single_value: {str(e)}")
            raise
    
    def test_connection(self) -> bool:
        """Testa conectividade com o banco"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                cursor.close()
                
                is_connected = result and result[0] == 1
                logger.info(f"Teste de conexão: {'✅ Sucesso' if is_connected else '❌ Falha'}")
                return is_connected
                
        except Exception as e:
            logger.error(f"Teste de conexão falhou: {str(e)}")
            return False
    
    def close(self):
        """Fecha pool de conexões"""
        try:
            if MySQLConnector._pool:
                MySQLConnector._pool = None
                logger.info("Pool MySQL fechado")
        except Exception as e:
            logger.error(f"Erro ao fechar pool: {str(e)}")

# Factory function para compatibilidade
def get_mysql_connector(**kwargs) -> MySQLConnector:
    """Factory function para criar instância do connector"""
    return MySQLConnector(**kwargs)