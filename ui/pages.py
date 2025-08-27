import streamlit as st
import pandas as pd
from typing import Dict, Any

from data.repository import DataRepository
from data.models import FilterParams
from core.analytics_engine import AnalyticsEngine
from config.settings import AppSettings
from .components import UIComponents
from .charts import ChartManager

class ExtratoPage:
    def __init__(self, repository: DataRepository, chart_manager: ChartManager, settings: AppSettings):
        self.repository = repository
        self.chart_manager = chart_manager
        self.settings = settings
    
    def render(self, filters: FilterParams):
        """Renderiza página de extratos"""
        UIComponents.render_section_title("📊 Dados de Extrato")
        
        with st.spinner("Carregando dados de extrato..."):
            df = self.repository.get_extract_data(filters)
        
        if df.empty:
            st.warning("Nenhum dado encontrado para os filtros selecionados.")
            return
        
        # Métricas principais
        self._render_extract_metrics(df)
        
        # Tabela de dados
        UIComponents.render_data_table(df, "Detalhes do Extrato")
        
        # Gráficos
        self._render_extract_charts(df)
    
    def _render_extract_metrics(self, df: pd.DataFrame):
        """Renderiza métricas do extrato"""
        creditos = df[df['tipo_lancamento'] == 'Crédito']['valor'].sum()
        debitos = abs(df[df['tipo_lancamento'] == 'Débito']['valor'].sum())
        saldo_final = df['valor'].sum()
        
        metrics = [
            {
                'title': 'Créditos',
                'value': UIComponents.format_currency(creditos),
                'change': f"{len(df[df['tipo_lancamento'] == 'Crédito'])} operações",
                'change_type': 'positive',
                'icon': '💰'
            },
            {
                'title': 'Débitos', 
                'value': UIComponents.format_currency(debitos),
                'change': f"{len(df[df['tipo_lancamento'] == 'Débito'])} operações",
                'change_type': 'negative',
                'icon': '💸'
            },
            {
                'title': 'Saldo Final',
                'value': UIComponents.format_currency(saldo_final),
                'change': f"{len(df)} operações totais",
                'change_type': 'positive' if saldo_final >= 0 else 'negative',
                'icon': '💼'
            }
        ]
        
        UIComponents.render_metrics_grid(metrics)
    
    def _render_extract_charts(self, df: pd.DataFrame):
        """Renderiza gráficos do extrato"""
        UIComponents.render_section_title("📈 Análises Gráficas")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Gráfico de operações por categoria
            fig_ops = self.chart_manager.create_operation_summary_chart(df)
            st.plotly_chart(fig_ops, use_container_width=True)
        
        with col2:
            # Gráfico por custodiante
            fig_cust = self.chart_manager.create_custodian_comparison_chart(df)
            st.plotly_chart(fig_cust, use_container_width=True)

class AnalysisPage:
    def __init__(self, analytics_engine: AnalyticsEngine, repository: DataRepository, 
                 chart_manager: ChartManager, settings: AppSettings):
        self.analytics_engine = analytics_engine
        self.repository = repository
        self.chart_manager = chart_manager
        self.settings = settings
    
    def render(self, filters: FilterParams):
        """Renderiza página de análises"""
        UIComponents.render_section_title("📈 Análises Avançadas")
        
        # Seletor de tipo de análise
        analysis_type = st.selectbox(
            "Tipo de Análise",
            ["Liquidez", "Concentração", "Evolução do Saldo"],
            key="analysis_type_selector"
        )
        
        if analysis_type == "Liquidez":
            self._render_liquidity_analysis(filters)
        elif analysis_type == "Concentração":
            self._render_concentration_analysis(filters)
        elif analysis_type == "Evolução do Saldo":
            self._render_balance_analysis(filters)
    
    def _render_liquidity_analysis(self, filters: FilterParams):
        """Renderiza análise de liquidez"""
        with st.spinner("Analisando liquidez..."):
            result = self.analytics_engine.analyze_liquidity(self.repository, filters)
        
        if not result.success:
            st.error(f"Erro na análise: {result.message}")
            return
        
        # Resumo
        if result.summary:
            st.info(result.summary)
        
        # Alertas
        if result.alerts:
            for alert in result.alerts:
                UIComponents.render_alert(
                    f"Alerta de Liquidez - {alert.fund}",
                    alert.message,
                    alert.severity
                )
        
        # Gráfico
        if result.data:
            fig = self.chart_manager.create_liquidity_analysis_chart(result.data)
            st.plotly_chart(fig, use_container_width=True)
    
    def _render_concentration_analysis(self, filters: FilterParams):
        """Renderiza análise de concentração"""
        with st.spinner("Analisando concentração..."):
            result = self.analytics_engine.analyze_concentration(self.repository, filters)
        
        if not result.success:
            st.error(f"Erro na análise: {result.message}")
            return
        
        # Resumo
        if result.summary:
            st.info(result.summary)
        
        # Alertas
        if result.alerts:
            for alert in result.alerts:
                UIComponents.render_alert(
                    f"Alerta de Concentração - {alert.fund}",
                    alert.message,
                    alert.severity
                )
        
        # Gráfico
        if result.data:
            fig = self.chart_manager.create_concentration_chart(result.data)
            st.plotly_chart(fig, use_container_width=True)
    
    def _render_balance_analysis(self, filters: FilterParams):
        """Renderiza análise de evolução do saldo"""
        with st.spinner("Analisando evolução do saldo..."):
            result = self.analytics_engine.analyze_balance_evolution(self.repository, filters)
        
        if not result.success:
            st.error(f"Erro na análise: {result.message}")
            return
        
        # Resumo
        if result.summary:
            st.info(result.summary)
        
        # Alertas
        if result.alerts:
            for alert in result.alerts:
                UIComponents.render_alert(
                    f"Alerta de Evolução - {alert.fund}",
                    alert.message,
                    alert.severity
                )
        
        # Gráfico
        if result.data:
            df_evolution = pd.DataFrame(result.data.get('evolution_data', []))
            if not df_evolution.empty:
                fig = self.chart_manager.create_balance_evolution_chart(df_evolution)
                st.plotly_chart(fig, use_container_width=True)

class MonitoringPage:
    def __init__(self, repository: DataRepository, settings: AppSettings):
        self.repository = repository
        self.settings = settings
    
    def render(self):
        """Renderiza página de monitoramento"""
        UIComponents.render_section_title("🔍 Monitoramento do Sistema")
        
        # Status do sistema
        st.subheader("Status da Conexão")
        
        if self.repository.is_connected():
            st.success("✅ Banco de dados conectado")
        else:
            st.error("❌ Banco de dados desconectado")
        
        # Informações do sistema
        st.subheader("Informações do Sistema")
        
        system_info = {
            "Cache TTL": f"{self.settings.analytics.cache_ttl} segundos",
            "Período padrão": f"{self.settings.analytics.default_period_days} dias",
            "Limite de registros": f"{self.settings.ui.max_records_display:,}",
            "Threshold de liquidez": f"{self.settings.analytics.liquidity_ratio_min} - {self.settings.analytics.liquidity_ratio_max}",
            "Threshold de concentração": f"{self.settings.analytics.concentration_threshold}%"
        }
        
        for key, value in system_info.items():
            st.metric(key, value)
        
        # Logs (placeholder)
        st.subheader("Logs Recentes")
        st.info("📝 Sistema de logs será implementado em próxima versão")