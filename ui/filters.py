import streamlit as st
from datetime import date, timedelta
from typing import List, Tuple, Optional
import pandas as pd

from data.repository import DataRepository

class FilterManager:
    def __init__(self, repository: DataRepository):
        self.repository = repository
    
    @st.cache_data(ttl=3600)
    def _get_available_funds(_self) -> List[str]:
        """Cache para fundos disponíveis"""
        return _self.repository.get_available_funds()
    
    @st.cache_data(ttl=3600)
    def _get_available_custodians(_self) -> List[str]:
        """Cache para custodiantes disponíveis"""
        return _self.repository.get_available_custodians()
    
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
        """Cria filtro de fundos"""
        st.markdown("**📈 Fundos**")
        
        available_funds = self._get_available_funds()
        
        if not available_funds:
            st.warning("Nenhum fundo disponível")
            return []
        
        select_all = st.checkbox("Todos os Fundos", value=False, key="all_funds")
        
        if select_all:
            return available_funds
        else:
            return st.multiselect(
                "Selecione fundos:",
                options=available_funds,
                key="selected_funds"
            )