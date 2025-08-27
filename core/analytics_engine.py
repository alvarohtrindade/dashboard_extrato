import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
import logging

from config.settings import AnalyticsConfig
from data.repository import DataRepository
from data.models import FilterParams
from .models import AnalysisResult, Alert, Metric

logger = logging.getLogger(__name__)

class AnalyticsEngine:
    def __init__(self, config: AnalyticsConfig):
        self.config = config
        self.rules = {}
    
    def load_rules(self, rules: Dict[str, Any]):
        """Carrega regras de análise"""
        self.rules = rules
    
    def analyze_liquidity(self, repository: DataRepository, filters: FilterParams) -> AnalysisResult:
        """Análise de liquidez"""
        try:
            # Buscar dados
            df_liquidity = repository.get_liquidity_metrics(filters)
            df_daily = repository.get_daily_metrics(filters)
            
            if df_liquidity.empty:
                return AnalysisResult("liquidity", success=False, message="Sem dados para análise")
            
            # Calcular métricas
            metrics = self._calculate_liquidity_metrics(df_liquidity)
            
            # Gerar alertas
            alerts = self._generate_liquidity_alerts(df_liquidity, metrics)
            
            # Preparar dados para visualização
            charts_data = self._prepare_liquidity_charts(df_liquidity, df_daily)
            
            return AnalysisResult(
                analysis_type="liquidity",
                success=True,
                metrics=metrics,
                alerts=alerts,
                data=charts_data,
                summary=self._create_liquidity_summary(metrics, alerts)
            )
            
        except Exception as e:
            logger.error(f"Erro na análise de liquidez: {e}")
            return AnalysisResult("liquidity", success=False, message=str(e))
    
    def analyze_concentration(self, repository: DataRepository, filters: FilterParams) -> AnalysisResult:
        """Análise de concentração"""
        try:
            df_concentration = repository.get_concentration_analysis(filters)
            
            if df_concentration.empty:
                return AnalysisResult("concentration", success=False, message="Sem dados para análise")
            
            metrics = self._calculate_concentration_metrics(df_concentration)
            alerts = self._generate_concentration_alerts(df_concentration, metrics)
            charts_data = self._prepare_concentration_charts(df_concentration)
            
            return AnalysisResult(
                analysis_type="concentration",
                success=True,
                metrics=metrics,
                alerts=alerts,
                data=charts_data,
                summary=self._create_concentration_summary(metrics, alerts)
            )
            
        except Exception as e:
            logger.error(f"Erro na análise de concentração: {e}")
            return AnalysisResult("concentration", success=False, message=str(e))
    
    def analyze_balance_evolution(self, repository: DataRepository, filters: FilterParams) -> AnalysisResult:
        """Análise de evolução do saldo"""
        try:
            df_daily = repository.get_daily_metrics(filters)
            
            if df_daily.empty:
                return AnalysisResult("balance_evolution", success=False, message="Sem dados para análise")
            
            # Calcular evolução do saldo
            df_evolution = self._calculate_balance_evolution(df_daily)
            
            metrics = self._calculate_evolution_metrics(df_evolution)
            alerts = self._generate_evolution_alerts(df_evolution, metrics)
            charts_data = self._prepare_evolution_charts(df_evolution)
            
            return AnalysisResult(
                analysis_type="balance_evolution",
                success=True,
                metrics=metrics,
                alerts=alerts,
                data=charts_data,
                summary=self._create_evolution_summary(metrics, alerts)
            )
            
        except Exception as e:
            logger.error(f"Erro na análise de evolução: {e}")
            return AnalysisResult("balance_evolution", success=False, message=str(e))
    
    def _calculate_liquidity_metrics(self, df: pd.DataFrame) -> Dict[str, Metric]:
        """Calcula métricas de liquidez"""
        metrics = {}
        
        for _, row in df.iterrows():
            fund_name = row['nmfundo']
            
            # Razão de liquidez
            liquidity_ratio = row['total_entries'] / abs(row['total_exits']) if row['total_exits'] != 0 else float('inf')
            
            # Status baseado nos thresholds
            if liquidity_ratio < self.config.liquidity_ratio_min:
                status = "Baixa"
                severity = "critical" if liquidity_ratio < 0.5 else "warning"
            elif liquidity_ratio > self.config.liquidity_ratio_max:
                status = "Alta"
                severity = "warning"
            else:
                status = "Normal"
                severity = "info"
            
            metrics[fund_name] = Metric(
                name=f"Liquidez - {fund_name}",
                value=liquidity_ratio,
                status=status,
                severity=severity,
                metadata={
                    'total_entries': row['total_entries'],
                    'total_exits': row['total_exits'],
                    'net_flow': row['net_flow'],
                    'operation_count': row['operation_count'],
                    'volatility': row.get('flow_volatility', 0)
                }
            )
        
        return metrics
    
    def _generate_liquidity_alerts(self, df: pd.DataFrame, metrics: Dict[str, Metric]) -> List[Alert]:
        """Gera alertas de liquidez"""
        alerts = []
        
        for fund_name, metric in metrics.items():
            if metric.severity in ['warning', 'critical']:
                alerts.append(Alert(
                    type="liquidity",
                    severity=metric.severity,
                    fund=fund_name,
                    message=f"Fundo {fund_name} com liquidez {metric.status.lower()}: {metric.value:.2f}",
                    value=metric.value,
                    metadata=metric.metadata
                ))
        
        return alerts
    
    def _calculate_concentration_metrics(self, df: pd.DataFrame) -> Dict[str, Metric]:
        """Calcula métricas de concentração"""
        metrics = {}
        
        # Concentração geral
        max_concentration = df['concentration_pct'].max() if not df.empty else 0
        high_concentration_funds = len(df[df['concentration_pct'] > self.config.concentration_threshold])
        
        metrics['overall'] = Metric(
            name="Concentração Geral",
            value=max_concentration,
            status="Alto" if max_concentration > self.config.concentration_threshold else "Normal",
            severity="warning" if max_concentration > self.config.concentration_threshold else "info",
            metadata={
                'high_concentration_funds': high_concentration_funds,
                'total_funds': len(df)
            }
        )
        
        # Métricas por fundo com alta concentração
        high_conc_funds = df[df['concentration_pct'] > 20]
        for _, row in high_conc_funds.iterrows():
            fund_name = row['nmfundo']
            metrics[fund_name] = Metric(
                name=f"Concentração - {fund_name}",
                value=row['concentration_pct'],
                status=row['concentration_level'],
                severity="critical" if row['concentration_pct'] > 30 else "warning",
                metadata={
                    'total_volume': row['total_volume'],
                    'operation_count': row['operation_count']
                }
            )
        
        return metrics
    
    def _generate_concentration_alerts(self, df: pd.DataFrame, metrics: Dict[str, Metric]) -> List[Alert]:
        """Gera alertas de concentração"""
        alerts = []
        
        for fund_name, metric in metrics.items():
            if fund_name != 'overall' and metric.severity in ['warning', 'critical']:
                alerts.append(Alert(
                    type="concentration",
                    severity=metric.severity,
                    fund=fund_name,
                    message=f"Alta concentração no fundo {fund_name}: {metric.value:.1f}%",
                    value=metric.value,
                    metadata=metric.metadata
                ))
        
        return alerts
    
    def _calculate_balance_evolution(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calcula evolução do saldo acumulado"""
        df_evolution = df.copy()
        df_evolution = df_evolution.sort_values(['nmfundo', 'date'])
        
        # Calcular saldo acumulado por fundo
        df_evolution['cumulative_flow'] = df_evolution.groupby('nmfundo')['daily_net_flow'].cumsum()
        
        # Calcular variação percentual
        df_evolution['pct_change'] = df_evolution.groupby('nmfundo')['cumulative_flow'].pct_change() * 100
        df_evolution['pct_change'] = df_evolution['pct_change'].replace([np.inf, -np.inf], np.nan).fillna(0)
        
        return df_evolution
    
    def _calculate_evolution_metrics(self, df: pd.DataFrame) -> Dict[str, Metric]:
        """Calcula métricas de evolução"""
        metrics = {}
        
        for fund in df['nmfundo'].unique():
            fund_data = df[df['nmfundo'] == fund]
            
            if len(fund_data) > 1:
                total_variation = fund_data['pct_change'].sum()
                volatility = fund_data['pct_change'].std()
                trend = "Positiva" if total_variation > 0 else "Negativa"
                
                metrics[fund] = Metric(
                    name=f"Evolução - {fund}",
                    value=total_variation,
                    status=trend,
                    severity="warning" if abs(total_variation) > 20 else "info",
                    metadata={
                        'volatility': volatility,
                        'periods': len(fund_data)
                    }
                )
        
        return metrics
    
    def _generate_evolution_alerts(self, df: pd.DataFrame, metrics: Dict[str, Metric]) -> List[Alert]:
        """Gera alertas de evolução"""
        alerts = []
        
        for fund_name, metric in metrics.items():
            if abs(metric.value) > 20:  # Variação maior que 20%
                alerts.append(Alert(
                    type="evolution",
                    severity="warning",
                    fund=fund_name,
                    message=f"Grande variação no saldo do fundo {fund_name}: {metric.value:.1f}%",
                    value=metric.value,
                    metadata=metric.metadata
                ))
        
        return alerts
    
    def _prepare_liquidity_charts(self, df_liquidity: pd.DataFrame, df_daily: pd.DataFrame) -> Dict[str, Any]:
        """Prepara dados para gráficos de liquidez"""
        return {
            'liquidity_metrics': df_liquidity.to_dict('records'),
            'daily_trends': df_daily.to_dict('records') if not df_daily.empty else [],
            'summary_stats': {
                'total_funds': len(df_liquidity),
                'avg_liquidity_ratio': df_liquidity['total_entries'].sum() / abs(df_liquidity['total_exits'].sum()) if df_liquidity['total_exits'].sum() != 0 else 0
            }
        }
    
    def _prepare_concentration_charts(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Prepara dados para gráficos de concentração"""
        return {
            'concentration_data': df.to_dict('records'),
            'summary_stats': {
                'max_concentration': df['concentration_pct'].max(),
                'funds_above_threshold': len(df[df['concentration_pct'] > self.config.concentration_threshold])
            }
        }
    
    def _prepare_evolution_charts(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Prepara dados para gráficos de evolução"""
        return {
            'evolution_data': df.to_dict('records'),
            'summary_stats': {
                'total_periods': len(df['date'].unique()),
                'funds_analyzed': len(df['nmfundo'].unique())
            }
        }
    
    def _create_liquidity_summary(self, metrics: Dict[str, Metric], alerts: List[Alert]) -> str:
        """Cria resumo da análise de liquidez"""
        total_funds = len(metrics)
        critical_funds = sum(1 for m in metrics.values() if m.severity == 'critical')
        warning_funds = sum(1 for m in metrics.values() if m.severity == 'warning')
        
        return f"Análise de {total_funds} fundos: {critical_funds} críticos, {warning_funds} com alertas"
    
    def _create_concentration_summary(self, metrics: Dict[str, Metric], alerts: List[Alert]) -> str:
        """Cria resumo da análise de concentração"""
        if 'overall' in metrics:
            max_conc = metrics['overall'].value
            return f"Concentração máxima: {max_conc:.1f}% - {len(alerts)} alertas gerados"
        return "Análise de concentração concluída"
    
    def _create_evolution_summary(self, metrics: Dict[str, Metric], alerts: List[Alert]) -> str:
        """Cria resumo da análise de evolução"""
        return f"Evolução de {len(metrics)} fundos analisada - {len(alerts)} alertas de variação"