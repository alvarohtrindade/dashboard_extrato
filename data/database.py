import logging
import pandas as pd
from typing import Optional, Tuple, Any
import mysql.connector
from mysql.connector import pooling
from sqlalchemy import create_engine, text
import time

from config.settings import DatabaseConfig

logger = logging.getLogger(__name__)

class DatabaseManager:
    _pool = None
    _engine = None
    _connection_available = False
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self._init_connections()
    
    def _init_connections(self):
        """Inicializa pool de conexões"""
        if DatabaseManager._pool is not None:
            self.pool = DatabaseManager._pool
            self.engine = DatabaseManager._engine
            self._connection_available = DatabaseManager._connection_available
            return
        
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Tentativa {attempt + 1} de conexão com o banco...")
                
                # Pool MySQL
                pool_config = {
                    'pool_name': 'dashboard_pool',
                    'pool_size': self.config.pool_size,
                    'pool_reset_session': True,
                    'host': self.config.host,
                    'user': self.config.user,
                    'password': self.config.password,
                    'database': self.config.database,
                    'port': self.config.port,
                    'charset': 'utf8mb4',
                    'collation': 'utf8mb4_unicode_ci',
                    'autocommit': True,
                    'connect_timeout': self.config.pool_timeout
                }
                
                DatabaseManager._pool = mysql.connector.pooling.MySQLConnectionPool(**pool_config)
                self.pool = DatabaseManager._pool
                
                # SQLAlchemy engine
                connection_string = (
                    f"mysql+pymysql://{self.config.user}:{self.config.password}"
                    f"@{self.config.host}:{self.config.port}/{self.config.database}"
                    f"?charset=utf8mb4&connect_timeout={self.config.pool_timeout}"
                )
                
                DatabaseManager._engine = create_engine(
                    connection_string,
                    pool_size=self.config.pool_size,
                    max_overflow=10,
                    pool_pre_ping=True,
                    pool_recycle=3600,
                    echo=False
                )
                self.engine = DatabaseManager._engine
                
                # Testar conexão
                test_conn = self.pool.get_connection()
                test_conn.ping(reconnect=True)
                test_conn.close()
                
                DatabaseManager._connection_available = True
                self._connection_available = True
                
                logger.info("Conexão com banco estabelecida com sucesso")
                return
                
            except Exception as e:
                logger.error(f"Tentativa {attempt + 1} falhou: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    logger.error("Falha na conexão com banco - modo offline")
                    DatabaseManager._connection_available = False
                    self._connection_available = False
    
    def is_connected(self) -> bool:
        """Verifica se há conexão disponível"""
        return self._connection_available and self.pool is not None
    
    def execute_query(self, query: str, params: Optional[Tuple] = None) -> pd.DataFrame:
        """Executa query e retorna DataFrame"""
        if not self.is_connected():
            logger.warning("Banco não disponível - retornando DataFrame vazio")
            return pd.DataFrame()
        
        try:
            with self.engine.connect() as conn:
                if params:
                    # Converter parâmetros para formato SQLAlchemy
                    param_dict = {f'param_{i}': param for i, param in enumerate(params)}
                    query_named = query
                    for i in range(len(params)):
                        query_named = query_named.replace('%s', f':param_{i}', 1)
                    
                    df = pd.read_sql(text(query_named), conn, params=param_dict)
                else:
                    df = pd.read_sql(text(query), conn)
                
                return df
                
        except Exception as e:
            logger.error(f"Erro ao executar query: {str(e)}")
            return pd.DataFrame()
    
    def execute_update(self, query: str, params: Optional[Tuple] = None) -> int:
        """Executa query de atualização"""
        if not self.is_connected():
            logger.warning("Banco não disponível - operação ignorada")
            return 0
        
        try:
            with self.engine.connect() as conn:
                if params:
                    param_dict = {f'param_{i}': param for i, param in enumerate(params)}
                    query_named = query
                    for i in range(len(params)):
                        query_named = query_named.replace('%s', f':param_{i}', 1)
                    
                    result = conn.execute(text(query_named), param_dict)
                else:
                    result = conn.execute(text(query))
                
                conn.commit()
                return result.rowcount
                
        except Exception as e:
            logger.error(f"Erro ao executar update: {str(e)}")
            return 0
    
    def close(self):
        """Fecha conexões"""
        try:
            if self.engine:
                self.engine.dispose()
                DatabaseManager._engine = None
            DatabaseManager._connection_available = False
            logger.info("Conexões fechadas")
        except Exception as e:
            logger.error(f"Erro ao fechar conexões: {str(e)}")