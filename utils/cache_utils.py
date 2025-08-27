"""
Sistema de cache inteligente para dashboard Streamlit
Otimizado para queries SQL e dados financeiros
"""
import streamlit as st
import hashlib
import json
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple, Callable
from datetime import datetime, timedelta
from functools import wraps

from .logging_utils import Log

logger = Log.get_logger(__name__)

class CacheManager:
    """Gerenciador de cache inteligente para dashboard"""
    
    @staticmethod
    def create_cache_key(*args, **kwargs) -> str:
        """Cria chave única para cache baseada em argumentos"""
        # Serializar argumentos de forma consistente
        cache_data = {
            'args': args,
            'kwargs': {k: v for k, v in kwargs.items() if k != 'self'}
        }
        
        # Converter para string JSON ordenada
        cache_str = json.dumps(cache_data, sort_keys=True, default=str)
        
        # Hash MD5 para chave compacta
        return hashlib.md5(cache_str.encode()).hexdigest()
    
    @staticmethod
    def cache_query_data(ttl: int = 1800):
        """Decorator para cache de dados de queries SQL"""
        def decorator(func: Callable):
            @wraps(func)
            @st.cache_data(ttl=ttl, show_spinner="Carregando dados...")
            def wrapper(*args, **kwargs):
                try:
                    result = func(*args, **kwargs)
                    if isinstance(result, pd.DataFrame) and not result.empty:
                        logger.debug(f"Cache hit para {func.__name__}: {len(result)} registros")
                    return result
                except Exception as e:
                    logger.error(f"Erro no cache {func.__name__}: {str(e)}")
                    return pd.DataFrame()
            return wrapper
        return decorator
    
    @staticmethod
    def cache_metrics(ttl: int = 300):
        """Decorator para cache de métricas em tempo real"""
        def decorator(func: Callable):
            @wraps(func)
            @st.cache_data(ttl=ttl, show_spinner="Calculando métricas...")
            def wrapper(*args, **kwargs):
                try:
                    result = func(*args, **kwargs)
                    logger.debug(f"Métricas calculadas para {func.__name__}")
                    return result
                except Exception as e:
                    logger.error(f"Erro ao calcular métricas {func.__name__}: {str(e)}")
                    return {}
            return wrapper
        return decorator
    
    @staticmethod
    def cache_static_data(ttl: int = 3600):
        """Decorator para dados que mudam pouco (fundos, custodiantes)"""
        def decorator(func: Callable):
            @wraps(func)
            @st.cache_data(ttl=ttl, hash_funcs={object: id})  # Use object ID for hashing
            def wrapper(*args, **kwargs):
                try:
                    result = func(*args, **kwargs)
                    logger.debug(f"Dados estáticos carregados: {func.__name__}")
                    return result
                except Exception as e:
                    logger.error(f"Erro ao carregar dados estáticos {func.__name__}: {str(e)}")
                    return []
            return wrapper
        return decorator
    
    @staticmethod
    def get_cache_stats() -> Dict[str, Any]:
        """Obtém estatísticas do cache atual"""
        try:
            cache_stats = {
                'cache_entries': len(st.session_state.get('_cache_data', {})),
                'last_clear': st.session_state.get('_cache_last_clear'),
                'memory_usage': 'N/A'  # Streamlit não expõe isso diretamente
            }
            return cache_stats
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas do cache: {str(e)}")
            return {}
    
    @staticmethod
    def clear_expired_cache():
        """Limpa cache expirado (executado automaticamente pelo Streamlit)"""
        try:
            st.cache_data.clear()
            st.session_state['_cache_last_clear'] = datetime.now()
            logger.info("Cache limpo com sucesso")
        except Exception as e:
            logger.error(f"Erro ao limpar cache: {str(e)}")

class PerformanceMonitor:
    """Monitor de performance para queries e operações"""
    
    @staticmethod
    def time_operation(operation_name: str):
        """Decorator para monitorar tempo de execução"""
        def decorator(func: Callable):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = datetime.now()
                
                try:
                    result = func(*args, **kwargs)
                    duration = (datetime.now() - start_time).total_seconds()
                    
                    # Log performance
                    if duration > 5.0:  # Operações lentas (> 5s)
                        logger.warning(f"Operação lenta - {operation_name}: {duration:.2f}s")
                    else:
                        logger.debug(f"Performance - {operation_name}: {duration:.2f}s")
                    
                    # Armazenar métricas na sessão
                    if '_performance_metrics' not in st.session_state:
                        st.session_state._performance_metrics = {}
                    
                    st.session_state._performance_metrics[operation_name] = {
                        'duration': duration,
                        'timestamp': datetime.now(),
                        'success': True
                    }
                    
                    return result
                    
                except Exception as e:
                    duration = (datetime.now() - start_time).total_seconds()
                    logger.error(f"Erro na operação {operation_name} após {duration:.2f}s: {str(e)}")
                    
                    if '_performance_metrics' not in st.session_state:
                        st.session_state._performance_metrics = {}
                    
                    st.session_state._performance_metrics[operation_name] = {
                        'duration': duration,
                        'timestamp': datetime.now(),
                        'success': False,
                        'error': str(e)
                    }
                    raise
                    
            return wrapper
        return decorator
    
    @staticmethod
    def get_performance_metrics() -> Dict[str, Any]:
        """Obtém métricas de performance da sessão"""
        return st.session_state.get('_performance_metrics', {})
    
    @staticmethod
    def clear_performance_metrics():
        """Limpa métricas de performance"""
        if '_performance_metrics' in st.session_state:
            del st.session_state._performance_metrics
        logger.info("Métricas de performance limpas")

# Decorators prontos para uso
cache_query = CacheManager.cache_query_data
cache_metrics = CacheManager.cache_metrics  
cache_static = CacheManager.cache_static_data
time_operation = PerformanceMonitor.time_operation