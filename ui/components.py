import streamlit as st
from typing import Dict, List, Optional

class UIComponents:
    
    @staticmethod
    def apply_global_styles():
        """Aplica estilos globais da aplicação"""
        st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
            
            html, body, [class*="css"] {
                font-family: 'Inter', sans-serif;
            }
            
            .metric-card {
                background: white;
                border-radius: 0.75rem;
                padding: 1.25rem;
                box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
                border: 1px solid #F0F0F0;
                margin-bottom: 1rem;
                transition: all 0.3s ease;
            }
            
            .metric-card:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
            }
            
            .metric-title {
                font-size: 0.875rem;
                color: #6E6E6E;
                margin-bottom: 0.5rem;
                font-weight: 500;
            }
            
            .metric-value {
                font-size: 1.5rem;
                font-weight: 700;
                color: #1E1E1E;
                margin-bottom: 0.25rem;
            }
            
            .metric-change {
                font-size: 0.75rem;
                font-weight: 500;
            }
            
            .positive { color: #2CB778; }
            .negative { color: #E74C3C; }
            .neutral { color: #F5B041; }
            
            .alert {
                padding: 1rem;
                border-radius: 0.5rem;
                margin-bottom: 1rem;
                display: flex;
                align-items: flex-start;
                gap: 0.75rem;
            }
            
            .alert-warning {
                background-color: rgba(245, 176, 65, 0.1);
                border-left: 4px solid #F5B041;
            }
            
            .alert-critical {
                background-color: rgba(231, 76, 60, 0.1);
                border-left: 4px solid #E74C3C;
            }
            
            .alert-info {
                background-color: rgba(44, 183, 120, 0.1);
                border-left: 4px solid #2CB778;
            }
            
            .section-title {
                font-size: 1.25rem;
                font-weight: 600;
                margin-bottom: 1rem;
                color: #343A40;
                padding-bottom: 0.5rem;
                border-bottom: 2px solid #E9ECEF;
            }
        </style>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def render_header(title: str, subtitle: str = ""):
        """Renderiza header da aplicação"""
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1E88E5 0%, #1565C0 100%);
                    padding: 1.5rem; border-radius: 0.75rem; margin-bottom: 1.5rem;
                    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1); color: white;">
            <h1 style="margin: 0; font-size: 2rem; font-weight: 600;">{title}</h1>
            <p style="margin: 0.5rem 0 0 0; opacity: 0.9; font-size: 1rem;">{subtitle}</p>
        </div>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def render_demo_credentials():
        """Renderiza credenciais de demonstração"""
        st.info("""
        **Credenciais de demonstração:**
        - **Admin:** usuário: `admin`, senha: `admin123`
        - **Gestor:** usuário: `gestor`, senha: `gestor123`  
        - **Usuário:** usuário: `usuario`, senha: `usuario123`
        """)
    
    @staticmethod
    def render_metric_card(title: str, value: str, change: str = "", 
                          change_type: str = "neutral", icon: str = ""):
        """Renderiza card de métrica"""
        change_class = f"change-{change_type}"
        change_html = f'<div class="metric-change {change_class}">{change}</div>' if change else ""
        icon_html = f'<div style="font-size: 1.5rem; margin-bottom: 0.5rem;">{icon}</div>' if icon else ""
        
        st.markdown(f"""
        <div class="metric-card">
            {icon_html}
            <div class="metric-title">{title}</div>
            <div class="metric-value">{value}</div>
            {change_html}
        </div>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def render_alert(title: str, message: str, alert_type: str = "warning"):
        """Renderiza alerta"""
        icon_map = {
            "warning": "⚠️",
            "critical": "🚨", 
            "info": "✅"
        }
        
        icon = icon_map.get(alert_type, "ℹ️")
        
        st.markdown(f"""
        <div class="alert alert-{alert_type}">
            <div style="font-size: 1.25rem;">{icon}</div>
            <div>
                <div style="font-weight: 600; margin-bottom: 0.25rem;">{title}</div>
                <div style="font-size: 0.875rem; opacity: 0.9;">{message}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def render_section_title(title: str):
        """Renderiza título de seção"""
        st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)
    
    @staticmethod
    def format_currency(value: float) -> str:
        """Formata valor como moeda brasileira"""
        if value is None or value != value:  # Check for None or NaN
            return "R$ 0,00"
        return f"R$ {value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    
    @staticmethod
    def format_percentage(value: float) -> str:
        """Formata valor como percentual"""
        if value is None or value != value:  # Check for None or NaN
            return "0,00%"
        return f"{value:.2f}%".replace('.', ',')
    
    @staticmethod
    def render_metrics_grid(metrics: List[Dict]):
        """Renderiza grid de métricas"""
        cols = st.columns(len(metrics))
        
        for i, metric in enumerate(metrics):
            with cols[i]:
                UIComponents.render_metric_card(
                    title=metric.get('title', ''),
                    value=metric.get('value', ''),
                    change=metric.get('change', ''),
                    change_type=metric.get('change_type', 'neutral'),
                    icon=metric.get('icon', '')
                )
    
    @staticmethod
    def render_data_table(df, title: str = "", height: int = 400):
        """Renderiza tabela de dados com título"""
        if title:
            UIComponents.render_section_title(title)
        
        if not df.empty:
            st.dataframe(df, use_container_width=True, height=height)
        else:
            st.info("Nenhum dado disponível para exibição")
    
    @staticmethod
    def render_loading_spinner(message: str = "Carregando dados..."):
        """Renderiza spinner de carregamento"""
        with st.spinner(message):
            return st.empty()