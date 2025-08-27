import streamlit as st
from datetime import date, timedelta
from typing import List, Tuple, Optional
import pandas as pd

from data.repository import DataRepository
from utils.cache_utils import cache_static, time_operation
from utils.logging_utils import Log

logger = Log.get_logger(__name__)

class FilterManager:
    def __init__(self, repository: DataRepository):
        self.repository = repository
    
    def _get_available_funds(self) -> List[str]:
        """Cache para fundos disponíveis com performance tracking"""
        # Usar cache simples via functools para evitar problemas com Streamlit
        if not hasattr(self, '_funds_cache'):
            try:
                funds = self.repository.get_available_funds()
                logger.info(f"Carregados {len(funds)} fundos disponíveis")
                self._funds_cache = funds
            except Exception as e:
                logger.error(f"Erro ao carregar fundos: {str(e)}")
                self._funds_cache = []
        return self._funds_cache
    
    def _get_available_custodians(self) -> List[str]:
        """Cache para custodiantes disponíveis com performance tracking"""
        # Usar cache simples via functools para evitar problemas com Streamlit
        if not hasattr(self, '_custodians_cache'):
            try:
                custodians = self.repository.get_available_custodians()
                logger.info(f"Carregados {len(custodians)} custodiantes disponíveis")
                self._custodians_cache = custodians
            except Exception as e:
                logger.error(f"Erro ao carregar custodiantes: {str(e)}")
                self._custodians_cache = []
        return self._custodians_cache
    
    def create_date_filter(self, default_days: int = 45) -> Tuple[date, date]:
        """Cria filtro de período"""
        st.markdown("**📅 Período**")
        
        max_date = date.today()
        default_start = max_date - timedelta(days=default_days)
        
        period_options = {
            "Hoje": 0,
            "Últimos 7 dias": 7,
            "Últimos 30 dias": 30,
            "Últimos 45 dias": 45,
            "Personalizado": -1
        }
        
        selected_preset = st.radio(
            "Escolha um período:",
            list(period_options.keys()),
            index=3,  # Default: 45 dias
            key="period_preset"
        )
        
        if selected_preset == "Personalizado":
            date_range = st.date_input(
                "Selecione o período:",
                value=(default_start, max_date),
                max_value=max_date,
                key="custom_date_range"
            )
            
            if isinstance(date_range, tuple) and len(date_range) == 2:
                start_date, end_date = date_range
            else:
                start_date = end_date = date_range if isinstance(date_range, date) else max_date
        else:
            days = period_options[selected_preset]
            start_date = max_date - timedelta(days=days)
            end_date = max_date
            st.info(f"Período: {start_date.strftime('%d/%m/%Y')} a {end_date.strftime('%d/%m/%Y')}")
        
        return start_date, end_date
    
    def create_custodian_filter(self) -> List[str]:
        """Cria filtro de custodiantes"""
        st.markdown("**🏦 Custodiantes**")
        
        available_custodians = self._get_available_custodians()
        
        if not available_custodians:
            st.warning("Nenhum custodiante disponível")
            return []
        
        select_all = st.checkbox("Todos os Custodiantes", value=True, key="all_custodians")
        
        if select_all:
            return available_custodians
        else:
            return st.multiselect(
                "Selecione custodiantes:",
                options=available_custodians,
                key="selected_custodians"
            )
    
    def create_fund_filter(self) -> List[str]:
        """Cria filtro de fundos com busca avançada"""
        st.markdown("**📈 Fundos**")
        
        available_funds = self._get_available_funds()
        
        if not available_funds:
            st.warning("Nenhum fundo disponível")
            return []
        
        # Filtro de busca
        search_term = st.text_input(
            "🔍 Buscar fundos:",
            placeholder="Digite para filtrar...",
            key="fund_search"
        )
        
        # Filtrar fundos baseado na busca
        if search_term:
            filtered_funds = [fund for fund in available_funds 
                            if search_term.lower() in fund.lower()]
            st.info(f"Encontrados {len(filtered_funds)} fundos")
        else:
            filtered_funds = available_funds
        
        # Opções de seleção
        col1, col2 = st.columns(2)
        with col1:
            select_all = st.checkbox("Todos", value=False, key="all_funds")
        with col2:
            clear_selection = st.button("Limpar", key="clear_funds")
        
        if clear_selection:
            st.session_state.selected_funds = []
            st.rerun()
        
        if select_all:
            selected_funds = filtered_funds
            # Atualizar session state
            st.session_state.selected_funds = selected_funds
        else:
            selected_funds = st.multiselect(
                "Selecione fundos:",
                options=filtered_funds,
                default=st.session_state.get('selected_funds', []),
                key="selected_funds"
            )
        
        # Mostrar resumo
        if selected_funds:
            st.success(f"✅ {len(selected_funds)} fundos selecionados")
        
        return selected_funds