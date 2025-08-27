import pandas as pd
import logging
from typing import List, Dict, Optional, Tuple
from datetime import date, datetime, timedelta

from .database import DatabaseManager
from .queries import QueryBuilder
from .models import FilterParams
from config.settings import DatabaseConfig

logger = logging.getLogger(__name__)

class DataRepository:
    def __init__(self, db_config: DatabaseConfig):
        self.db = DatabaseManager(db_config)
        self.query_builder = QueryBuilder()
    
    def get_extract_data(self, filters: FilterParams) -> pd.DataFrame:
        """Busca dados de extrato com filtros aplicados"""
        try:
            query, params = self.query_builder.build_extract_query(filters)
            df = self.db.execute_query(query, params)
            if not df.empty:
                df = self._process_extract_data(df)
            return df
        except Exception as e:
            logger.error(f"Erro ao buscar dados de extrato: {e}")
            return pd.DataFrame()
    
    def get_available_funds(self) -> List[str]:
        """Retorna lista de fundos disponíveis"""
        query = """
        SELECT DISTINCT nmfundo 
        FROM DW_STAGING.vw_extrato 
        WHERE nmfundo IS NOT NULL 
        AND nmfundo != ''
        ORDER BY nmfundo
        LIMIT 1000
        """
        
        try:
            df = self.db.execute_query(query)
            return df['nmfundo'].tolist() if not df.empty else []
        except Exception as e:
            logger.error(f"Erro ao buscar fundos: {e}")
            return []
    
    def get_available_custodians(self) -> List[str]:
        """Retorna lista de custodiantes disponíveis"""
        query = """
        SELECT DISTINCT fonte 
        FROM DW_STAGING.vw_extrato 
        WHERE fonte IS NOT NULL 
        AND fonte != ''
        ORDER BY fonte
        """
        
        try:
            df = self.db.execute_query(query)
            return df['fonte'].tolist() if not df.empty else []
        except Exception as e:
            logger.error(f"Erro ao buscar custodiantes: {e}")
            return []
    
    def get_liquidity_metrics(self, filters: FilterParams) -> pd.DataFrame:
        """Busca métricas de liquidez"""
        try:
            query, params = self.query_builder.build_liquidity_query(filters)
            return self.db.execute_query(query, params)
        except Exception as e:
            logger.error(f"Erro ao buscar métricas de liquidez: {e}")
            return pd.DataFrame()
    
    def get_daily_metrics(self, filters: FilterParams) -> pd.DataFrame:
        """Busca métricas diárias para análise de tendências"""
        try:
            query, params = self.query_builder.build_daily_metrics_query(filters)
            df = self.db.execute_query(query, params)
            if not df.empty:
                df['date'] = pd.to_datetime(df['date'])
                df = df.sort_values(['date', 'nmfundo'])
            return df
        except Exception as e:
            logger.error(f"Erro ao buscar métricas diárias: {e}")
            return pd.DataFrame()
    
    def get_concentration_analysis(self, filters: FilterParams) -> pd.DataFrame:
        """Análise de concentração por fundo"""
        try:
            query, params = self.query_builder.build_concentration_query(filters)
            return self.db.execute_query(query, params)
        except Exception as e:
            logger.error(f"Erro ao buscar análise de concentração: {e}")
            return pd.DataFrame()
    
    def execute_custom_analysis(self, rule_queries: Dict[str, str], filters: FilterParams) -> Dict[str, pd.DataFrame]:
        """Executa análises customizadas baseadas em regras"""
        results = {}
        
        for analysis_name, query_template in rule_queries.items():
            try:
                # Aplicar filtros na query
                query, params = self._apply_filters_to_query(query_template, filters)
                df = self.db.execute_query(query, params)
                results[analysis_name] = df
            except Exception as e:
                logger.error(f"Erro na análise {analysis_name}: {e}")
                results[analysis_name] = pd.DataFrame()
        
        return results
    
    def _process_extract_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Processa dados de extrato adicionando campos calculados"""
        # Converter tipos
        df['dt_lancamento'] = pd.to_datetime(df['dt_lancamento'])
        df['entrada'] = pd.to_numeric(df['entrada'], errors='coerce').fillna(0)
        df['saida'] = pd.to_numeric(df['saida'], errors='coerce').fillna(0)
        df['saldo'] = pd.to_numeric(df['saldo'], errors='coerce').fillna(0)
        
        # Campos calculados
        df['valor'] = df['entrada'] - df['saida']
        df['tipo_lancamento'] = df.apply(self._determine_operation_type, axis=1)
        df['categoria'] = df['lancamento'].apply(self._categorize_operation)
        df['data'] = df['dt_lancamento'].dt.date
        
        # Campos auxiliares
        df['mes_ano'] = df['dt_lancamento'].dt.to_period('M').astype(str)
        df['ano'] = df['dt_lancamento'].dt.year
        df['mes'] = df['dt_lancamento'].dt.month
        
        return df
    
    def _determine_operation_type(self, row) -> str:
        """Determina tipo de operação baseado nos valores"""
        if row['entrada'] > 0:
            return 'Crédito'
        elif row['saida'] > 0:
            return 'Débito'
        else:
            return 'Neutro'
    
    def _categorize_operation(self, description: str) -> str:
        """Categoriza operação baseada na descrição"""
        if pd.isna(description):
            return 'Outros'
        
        description_lower = description.lower()
        
        # Mapeamento de categorias
        category_mapping = {
            'taxa': ['taxa', 'fee', 'tarifa'],
            'aplicação': ['aplic', 'aplicação', 'aporte'],
            'resgate': ['resgate', 'saque', 'redenção'],
            'rendimento': ['rendimento', 'juros', 'yield'],
            'transferência': ['transfer', 'moviment'],
            'compra': ['compra', 'purchase'],
            'venda': ['venda', 'sale'],
        }
        
        for category, keywords in category_mapping.items():
            if any(keyword in description_lower for keyword in keywords):
                return category.title()
        
        return 'Outros'
    
    def _apply_filters_to_query(self, query_template: str, filters: FilterParams) -> Tuple[str, Tuple]:
        """Aplica filtros dinâmicos à query e retorna query + parâmetros"""
        query = query_template
        params = [filters.start_date, filters.end_date]
        
        # Filtro de fundos
        if filters.funds:
            fund_placeholders = ','.join(['%s'] * len(filters.funds))
            fund_filter = f"AND nmfundo IN ({fund_placeholders})"
            params.extend(filters.funds)
        else:
            fund_filter = ""
        
        # Filtro de custodiantes
        if filters.custodians:
            custodian_placeholders = ','.join(['%s'] * len(filters.custodians))
            custodian_filter = f"AND fonte IN ({custodian_placeholders})"
            params.extend(filters.custodians)
        else:
            custodian_filter = ""
        
        # Substituir placeholders
        query = query.replace('{fund_filter}', fund_filter)
        query = query.replace('{custodian_filter}', custodian_filter)
        
        return query, tuple(params)
    
    def is_connected(self) -> bool:
        """Verifica se há conexão com o banco"""
        return self.db.is_connected()
    
    def close(self):
        """Fecha conexões"""
        self.db.close()