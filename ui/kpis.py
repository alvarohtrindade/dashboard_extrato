"""
Componente de KPIs financeiros em tempo real
Análise crítica de negócio para fundos de investimento
"""
import streamlit as st
import pandas as pd
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from data.models import FilterParams
from data.repository import DataRepository
from utils.logging_utils import Log

logger = Log.get_logger(__name__)

class KPIManager:
    """Gerenciador de KPIs financeiros críticos"""
    
    def __init__(self, repository: DataRepository):
        self.repository = repository
    
    def calculate_financial_kpis(self, filters: FilterParams) -> Dict[str, Any]:
        """Calcula KPIs financeiros essenciais"""
        # Cache simples usando session_state
        import streamlit as st
        cache_key = f"kpis_{filters.start_date}_{filters.end_date}_{hash(str(filters.funds))}"
        
        if cache_key in st.session_state:
            return st.session_state[cache_key]
        
        try:
            # Query principal para dados do período
            query_data = self.repository.get_extract_data(filters)
            
            if query_data.empty:
                return self._empty_kpis()
            
            # KPIs básicos
            total_entries = query_data['entrada'].sum() if 'entrada' in query_data else 0
            total_exits = query_data['saida'].sum() if 'saida' in query_data else 0
            net_flow = total_entries - total_exits
            
            # Análise de liquidez
            liquidity_metrics = self._calculate_liquidity_metrics(query_data)
            
            # Análise de concentração
            concentration_metrics = self._calculate_concentration_metrics(query_data)
            
            # Análise de performance
            performance_metrics = self._calculate_performance_metrics(query_data, filters)
            
            kpis = {
                # KPIs Principais
                'total_volume': abs(total_entries) + abs(total_exits),
                'net_flow': net_flow,
                'total_entries': total_entries,
                'total_exits': total_exits,
                'operation_count': len(query_data),
                'active_funds': query_data['nmfundo'].nunique() if 'nmfundo' in query_data else 0,
                
                # Métricas de liquidez
                **liquidity_metrics,
                
                # Métricas de concentração
                **concentration_metrics,
                
                # Métricas de performance
                **performance_metrics,
                
                # Metadados
                'last_update': datetime.now(),
                'period_days': (filters.end_date - filters.start_date).days,
                'data_quality_score': self._calculate_data_quality_score(query_data)
            }
            
            logger.info(f"KPIs calculados: {len(kpis)} métricas para {len(query_data)} registros")
            
            # Cache o resultado
            st.session_state[cache_key] = kpis
            return kpis
            
        except Exception as e:
            logger.error(f"Erro ao calcular KPIs: {str(e)}")
            return self._empty_kpis()
    
    def _calculate_liquidity_metrics(self, data: pd.DataFrame) -> Dict[str, float]:
        """Calcula métricas críticas de liquidez"""
        try:
            if data.empty or 'saldo' not in data:
                return {'liquidity_ratio': 0, 'min_balance': 0, 'avg_balance': 0}
            
            # Saldos por fundo
            balance_data = data.groupby('nmfundo')['saldo'].agg(['min', 'max', 'mean']).reset_index()
            
            # Ratio de liquidez (saldo mínimo / médio)
            liquidity_ratio = (balance_data['min'].sum() / balance_data['mean'].sum()) if balance_data['mean'].sum() > 0 else 0
            
            # Fundos com saldo crítico (< 10% do saldo médio)
            critical_funds = len(balance_data[balance_data['min'] < (balance_data['mean'] * 0.1)])
            
            return {
                'liquidity_ratio': round(liquidity_ratio, 4),
                'min_balance': balance_data['min'].min(),
                'avg_balance': balance_data['mean'].mean(),
                'critical_funds_count': critical_funds,
                'liquidity_risk_level': 'Alto' if liquidity_ratio < 0.5 else 'Médio' if liquidity_ratio < 0.8 else 'Baixo'
            }
            
        except Exception as e:
            logger.error(f"Erro ao calcular métricas de liquidez: {str(e)}")
            return {'liquidity_ratio': 0, 'liquidity_risk_level': 'Desconhecido'}
    
    def _calculate_concentration_metrics(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Calcula métricas de concentração de risco"""
        try:
            if data.empty or 'nmfundo' not in data:
                return {'concentration_index': 0, 'top_fund_percentage': 0}
            
            # Volume por fundo
            fund_volumes = data.groupby('nmfundo').agg({
                'entrada': 'sum',
                'saida': 'sum'
            }).reset_index()
            
            fund_volumes['total_volume'] = fund_volumes['entrada'].abs() + fund_volumes['saida'].abs()
            total_volume = fund_volumes['total_volume'].sum()
            
            if total_volume == 0:
                return {'concentration_index': 0, 'top_fund_percentage': 0}
            
            # Percentual do maior fundo
            fund_volumes['percentage'] = (fund_volumes['total_volume'] / total_volume * 100)
            top_fund_pct = fund_volumes['percentage'].max()
            
            # Índice de concentração Herfindahl
            concentration_index = (fund_volumes['percentage'] ** 2).sum() / 100
            
            # Top 3 fundos
            top_3_pct = fund_volumes.nlargest(3, 'percentage')['percentage'].sum()
            
            return {
                'concentration_index': round(concentration_index, 2),
                'top_fund_percentage': round(top_fund_pct, 2),
                'top_3_funds_percentage': round(top_3_pct, 2),
                'concentration_risk_level': 'Alto' if top_fund_pct > 50 else 'Médio' if top_fund_pct > 30 else 'Baixo'
            }
            
        except Exception as e:
            logger.error(f"Erro ao calcular concentração: {str(e)}")
            return {'concentration_index': 0, 'concentration_risk_level': 'Desconhecido'}
    
    def _calculate_performance_metrics(self, data: pd.DataFrame, filters: FilterParams) -> Dict[str, Any]:
        """Calcula métricas de performance operacional"""
        try:
            if data.empty:
                return {'daily_avg_operations': 0, 'operational_efficiency': 0}
            
            period_days = max((filters.end_date - filters.start_date).days, 1)
            
            # Operações por dia
            daily_avg_operations = len(data) / period_days
            
            # Eficiência operacional (ratio entrada/saída)
            total_entries = data['entrada'].sum() if 'entrada' in data else 0
            total_exits = data['saida'].sum() if 'saida' in data else 0
            operational_efficiency = abs(total_entries / total_exits) if total_exits != 0 else 0
            
            # Volatilidade de fluxo
            if 'dt_lancamento' in data:
                daily_flows = data.groupby(data['dt_lancamento'].dt.date).agg({
                    'entrada': 'sum',
                    'saida': 'sum'
                }).reset_index()
                daily_flows['net_flow'] = daily_flows['entrada'] - daily_flows['saida']
                flow_volatility = daily_flows['net_flow'].std() if len(daily_flows) > 1 else 0
            else:
                flow_volatility = 0
            
            return {
                'daily_avg_operations': round(daily_avg_operations, 2),
                'operational_efficiency': round(operational_efficiency, 4),
                'flow_volatility': round(flow_volatility, 2),
                'operational_health': 'Boa' if daily_avg_operations > 10 and operational_efficiency > 0.8 else 'Regular' if daily_avg_operations > 5 else 'Baixa'
            }
            
        except Exception as e:
            logger.error(f"Erro ao calcular performance: {str(e)}")
            return {'daily_avg_operations': 0, 'operational_health': 'Desconhecida'}
    
    def _calculate_data_quality_score(self, data: pd.DataFrame) -> float:
        """Calcula score de qualidade dos dados"""
        try:
            if data.empty:
                return 0.0
            
            quality_score = 100.0
            
            # Penalizações por problemas de qualidade
            if data.isnull().sum().sum() > 0:
                null_percentage = (data.isnull().sum().sum() / data.size) * 100
                quality_score -= null_percentage * 2
            
            # Verificar consistência de saldos
            if 'saldo' in data and (data['saldo'] < 0).sum() > len(data) * 0.1:
                quality_score -= 10  # Muitos saldos negativos
            
            # Verificar datas futuras
            if 'dt_lancamento' in data:
                future_dates = (data['dt_lancamento'] > datetime.now()).sum()
                if future_dates > 0:
                    quality_score -= 20
            
            return max(0.0, min(100.0, quality_score))
            
        except Exception as e:
            logger.error(f"Erro ao calcular qualidade dos dados: {str(e)}")
            return 50.0  # Score neutro em caso de erro
    
    def _empty_kpis(self) -> Dict[str, Any]:
        """Retorna KPIs vazios para casos de erro"""
        return {
            'total_volume': 0,
            'net_flow': 0,
            'total_entries': 0,
            'total_exits': 0,
            'operation_count': 0,
            'active_funds': 0,
            'liquidity_ratio': 0,
            'concentration_index': 0,
            'daily_avg_operations': 0,
            'data_quality_score': 0,
            'last_update': datetime.now(),
            'liquidity_risk_level': 'Desconhecido',
            'concentration_risk_level': 'Desconhecido',
            'operational_health': 'Desconhecida'
        }
    
    def render_kpi_dashboard(self, kpis: Dict[str, Any]):
        """Renderiza dashboard de KPIs"""
        st.markdown("### 📊 **Indicadores Financeiros em Tempo Real**")
        
        # Linha 1: KPIs principais
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="💰 Volume Total",
                value=f"R$ {kpis['total_volume']:,.0f}",
                delta=f"R$ {kpis['net_flow']:,.0f}" if kpis['net_flow'] != 0 else None
            )
        
        with col2:
            st.metric(
                label="🔄 Operações",
                value=f"{kpis['operation_count']:,}",
                delta=f"{kpis['daily_avg_operations']:.1f}/dia"
            )
        
        with col3:
            liquidity_color = "normal" if kpis.get('liquidity_risk_level') == 'Baixo' else "inverse"
            st.metric(
                label="💧 Liquidez",
                value=f"{kpis['liquidity_ratio']:.2%}",
                delta=kpis.get('liquidity_risk_level', 'N/A'),
                delta_color=liquidity_color
            )
        
        with col4:
            concentration_color = "inverse" if kpis.get('concentration_risk_level') == 'Alto' else "normal"
            st.metric(
                label="🎯 Concentração",
                value=f"{kpis['concentration_index']:.1f}%",
                delta=kpis.get('concentration_risk_level', 'N/A'),
                delta_color=concentration_color
            )
        
        # Linha 2: Métricas de risco
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="📈 Fundos Ativos",
                value=kpis['active_funds'],
                delta=f"{kpis.get('critical_funds_count', 0)} críticos" if kpis.get('critical_funds_count') else None
            )
        
        with col2:
            st.metric(
                label="⚡ Eficiência",
                value=f"{kpis.get('operational_efficiency', 0):.2f}",
                delta=kpis.get('operational_health', 'N/A')
            )
        
        with col3:
            quality_color = "normal" if kpis['data_quality_score'] > 80 else "inverse"
            st.metric(
                label="📋 Qualidade",
                value=f"{kpis['data_quality_score']:.0f}%",
                delta_color=quality_color
            )
        
        with col4:
            st.metric(
                label="📅 Período",
                value=f"{kpis.get('period_days', 0)} dias",
                delta=kpis['last_update'].strftime('%H:%M')
            )
        
        # Alertas críticos
        self._render_critical_alerts(kpis)
    
    def _render_critical_alerts(self, kpis: Dict[str, Any]):
        """Renderiza alertas críticos baseados nos KPIs"""
        alerts = []
        
        # Alertas de liquidez
        if kpis.get('liquidity_risk_level') == 'Alto':
            alerts.append("🚨 **Risco de Liquidez Alto** - Saldos críticos detectados")
        
        # Alertas de concentração
        if kpis.get('concentration_risk_level') == 'Alto':
            alerts.append("⚠️ **Alta Concentração** - Risco concentrado em poucos fundos")
        
        # Alertas de qualidade
        if kpis['data_quality_score'] < 70:
            alerts.append("📋 **Qualidade de Dados Baixa** - Verificar inconsistências")
        
        # Alertas operacionais
        if kpis.get('operational_health') == 'Baixa':
            alerts.append("⚡ **Baixa Atividade Operacional** - Poucas operações no período")
        
        if alerts:
            st.markdown("### 🚨 Alertas Críticos")
            for alert in alerts:
                st.warning(alert)