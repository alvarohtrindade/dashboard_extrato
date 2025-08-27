import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from typing import Dict, Any, List

class ChartManager:
    
    @staticmethod
    def create_balance_evolution_chart(df: pd.DataFrame) -> go.Figure:
        """Cria gráfico de evolução do saldo"""
        if df.empty:
            return go.Figure()
        
        fig = px.line(
            df, 
            x='date', 
            y='cumulative_flow',
            color='nmfundo',
            title="Evolução do Saldo Acumulado",
            labels={'date': 'Data', 'cumulative_flow': 'Saldo Acumulado (R$)', 'nmfundo': 'Fundo'}
        )
        
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            height=450
        )
        
        return fig
    
    @staticmethod
    def create_liquidity_analysis_chart(data: Dict[str, Any]) -> go.Figure:
        """Cria gráfico de análise de liquidez"""
        if not data.get('liquidity_metrics'):
            return go.Figure()
        
        df = pd.DataFrame(data['liquidity_metrics'])
        
        # Calcular razão de liquidez
        df['liquidity_ratio'] = df['total_entries'] / df['total_exits'].abs()
        df['liquidity_ratio'] = df['liquidity_ratio'].replace([float('inf'), -float('inf')], 0)
        
        fig = px.scatter(
            df,
            x='nmfundo',
            y='liquidity_ratio',
            size='operation_count',
            title="Análise de Liquidez por Fundo",
            labels={'nmfundo': 'Fundo', 'liquidity_ratio': 'Razão de Liquidez'}
        )
        
        # Linha de referência
        fig.add_hline(y=1.0, line_dash="dash", line_color="red", 
                     annotation_text="Equilíbrio")
        
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            height=450
        )
        
        return fig
    
    @staticmethod
    def create_concentration_chart(data: Dict[str, Any]) -> go.Figure:
        """Cria gráfico de concentração"""
        if not data.get('concentration_data'):
            return go.Figure()
        
        df = pd.DataFrame(data['concentration_data'])
        
        fig = px.bar(
            df.sort_values('concentration_pct', ascending=False).head(10),
            x='nmfundo',
            y='concentration_pct',
            color='concentration_level',
            title="Concentração por Fundo (%)",
            labels={'nmfundo': 'Fundo', 'concentration_pct': 'Concentração (%)'}
        )
        
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            height=450
        )
        
        return fig
    
    @staticmethod
    def create_operation_summary_chart(df: pd.DataFrame) -> go.Figure:
        """Cria gráfico de resumo de operações"""
        if df.empty or 'categoria' not in df.columns:
            return go.Figure()
        
        category_summary = df.groupby('categoria')['valor'].agg(['sum', 'count']).reset_index()
        category_summary['valor_abs'] = category_summary['sum'].abs()
        
        fig = px.pie(
            category_summary,
            values='valor_abs',
            names='categoria',
            title="Composição por Tipo de Operação",
            hole=0.4
        )
        
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            height=450
        )
        
        return fig
    
    @staticmethod
    def create_custodian_comparison_chart(df: pd.DataFrame) -> go.Figure:
        """Cria gráfico de comparação entre custodiantes"""
        if df.empty or 'fonte' not in df.columns:
            return go.Figure()
        
        custodian_summary = df.groupby('fonte').agg({
            'valor': 'sum',
            'nmfundo': 'nunique'
        }).reset_index()
        
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=["Volume por Custodiante", "Número de Fundos"],
            specs=[[{"type": "bar"}, {"type": "pie"}]]
        )
        
        # Volume por custodiante
        fig.add_trace(
            go.Bar(
                x=custodian_summary['fonte'],
                y=custodian_summary['valor'].abs(),
                name="Volume"
            ),
            row=1, col=1
        )
        
        # Distribuição de fundos
        fig.add_trace(
            go.Pie(
                labels=custodian_summary['fonte'],
                values=custodian_summary['nmfundo'],
                name="Fundos"
            ),
            row=1, col=2
        )
        
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            height=450,
            showlegend=False
        )
        
        return fig