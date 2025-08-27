import streamlit as st
from datetime import date, timedelta
from typing import Optional

from core.auth_service import AuthService
from core.analytics_engine import AnalyticsEngine
from data.repository import DataRepository
from data.models import FilterParams
from config.settings import AppSettings
from core.models import DashboardState
from .components import UIComponents
from .filters import FilterManager
from .charts import ChartManager
from .pages import ExtratoPage, AnalysisPage, MonitoringPage
from .kpis import KPIManager

class Dashboard:
    def __init__(self, auth_service: AuthService, repository: DataRepository, 
                 analytics_engine: AnalyticsEngine, settings: AppSettings):
        self.auth_service = auth_service
        self.repository = repository
        self.analytics_engine = analytics_engine
        self.settings = settings
        self.filter_manager = FilterManager(repository)
        self.chart_manager = ChartManager()
        self.kpi_manager = KPIManager(repository)
        
        # Inicializar estado
        self._init_session_state()
    
    def _init_session_state(self):
        """Inicializa estado da sessão"""
        if 'dashboard_state' not in st.session_state:
            st.session_state.dashboard_state = DashboardState()
    
    def run(self):
        """Executa a aplicação"""
        state = st.session_state.dashboard_state
        
        if not state.authenticated:
            self._render_login_page()
        else:
            self._render_main_dashboard()
    
    def _render_login_page(self):
        """Renderiza página de login"""
        UIComponents.render_header("Painel Catálise - Extratos", 
                                 "Gestão em tempo real de liquidez e compliance")
        
        # Verificar modo demo
        if not self.repository.is_connected():
            st.warning("⚠️ Modo Demo - Banco de dados não disponível")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            # Container principal de login
            st.markdown("""
            <div style="background: white; border-radius: 12px; padding: 2rem; 
                        box-shadow: 0 4px 20px rgba(0,0,0,0.1); margin: 2rem 0;">
                <h2 style="text-align: center; color: #1E3A8A; margin-bottom: 2rem;">
                    🔐 Acesso ao Sistema
                </h2>
            </div>
            """, unsafe_allow_html=True)
            
            # Opção 1: Login Microsoft (se habilitado)
            if self.auth_service.is_microsoft_enabled():
                st.markdown("### 🔷 Login Corporativo")
                
                # Tentar autenticação Microsoft
                microsoft_user = self.auth_service.authenticate_microsoft()
                if microsoft_user:
                    st.session_state.dashboard_state.authenticated = True
                    st.session_state.dashboard_state.current_user = microsoft_user
                    st.success(f"✅ Login realizado com sucesso! Bem-vindo, {microsoft_user.full_name}")
                    st.rerun()
                
                st.markdown("---")
                st.markdown("### 🔑 Login Tradicional")
            
            # Opção 2: Login tradicional (sempre disponível)
            with st.form("login_form"):
                username = st.text_input("Usuário", placeholder="Digite seu usuário")
                password = st.text_input("Senha", type="password", placeholder="Digite sua senha")
                submitted = st.form_submit_button("Entrar", type="primary", use_container_width=True)
                
                if submitted and username and password:
                    user = self.auth_service.authenticate(username, password)
                    if user:
                        st.session_state.dashboard_state.authenticated = True
                        st.session_state.dashboard_state.current_user = user
                        st.success("✅ Login realizado com sucesso!")
                        st.rerun()
                    else:
                        st.error("❌ Usuário ou senha inválidos!")
            
            # Informações adicionais
            with st.expander("ℹ️ Informações de Acesso"):
                if self.auth_service.is_microsoft_enabled():
                    st.info("""
                    **🔷 Login Corporativo:**
                    - Use sua conta Microsoft/Office 365 da empresa
                    - Acesso baseado no seu perfil organizacional
                    """)
                
                if not self.repository.is_connected():
                    UIComponents.render_demo_credentials()
                
                st.info("""
                **📊 Recursos Disponíveis:**
                - Visualização de extratos de todos os custodiantes
                - Filtros por período e múltiplos fundos
                - Análise de liquidez e desenquadramento
                - Monitoramento em tempo real
                """)
        
        # Verificar se há erro de autenticação
        if 'auth_error' in st.session_state:
            st.error(st.session_state.auth_error)
            del st.session_state.auth_error
    
    def _render_main_dashboard(self):
        """Renderiza dashboard principal"""
        state = st.session_state.dashboard_state
        
        # Header
        self._render_dashboard_header(state.current_user)
        
        # Sidebar com filtros
        with st.sidebar:
            self._render_sidebar_filters()
        
        # KPIs em tempo real (sempre visível)
        current_filters = self._get_current_filters()
        kpis = self.kpi_manager.calculate_financial_kpis(current_filters)
        self.kpi_manager.render_kpi_dashboard(kpis)
        
        st.markdown("---")
        
        # Tabs principais
        tab1, tab2, tab3 = st.tabs(["📊 Extratos", "📈 Análises", "🔍 Monitoramento"])
        
        with tab1:
            extrato_page = ExtratoPage(self.repository, self.chart_manager, self.settings)
            extrato_page.render(self._get_current_filters())
        
        with tab2:
            analysis_page = AnalysisPage(self.analytics_engine, self.repository, self.chart_manager, self.settings)
            analysis_page.render(self._get_current_filters())
        
        with tab3:
            if state.current_user.has_permission(['admin', 'gestor']):
                monitoring_page = MonitoringPage(self.repository, self.settings)
                monitoring_page.render()
            else:
                st.warning("⚠️ Você não tem permissão para acessar esta área.")
    
    def _render_dashboard_header(self, user):
        """Renderiza header do dashboard"""
        col1, col2, col3 = st.columns([6, 2, 1])
        
        with col1:
            st.markdown(f"""
            <h1 style="color: #1E3A8A; margin-bottom: 0;">Dashboard de Extratos</h1>
            <p style="color: #64748B; margin-top: 0;">Liquidez | Compliance | Performance</p>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div style="text-align: right;">
                <p style="margin-bottom: 0;"><strong>Bem-vindo, {user.full_name}!</strong></p>
                <p style="color: #64748B; margin-top: 0;">Perfil: {user.profile.title()}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            if st.button("🚪 Sair"):
                self.auth_service.logout()
                st.session_state.dashboard_state = DashboardState()
                st.rerun()
    
    def _render_sidebar_filters(self):
        """Renderiza filtros na sidebar"""
        st.markdown("### Filtros")
        
        # Período
        date_range = self.filter_manager.create_date_filter(
            default_days=self.settings.analytics.default_period_days
        )
        st.session_state.dashboard_state.date_range = date_range
        
        # Custodiantes
        custodians = self.filter_manager.create_custodian_filter()
        st.session_state.dashboard_state.selected_custodians = custodians
        
        # Fundos
        funds = self.filter_manager.create_fund_filter()
        st.session_state.dashboard_state.selected_funds = funds
        
        # Botão de atualização
        st.markdown("---")
        if st.button("🔄 Atualizar Dados"):
            st.cache_data.clear()
            st.rerun()
    
    def _get_current_filters(self) -> FilterParams:
        """Obtém filtros atuais da sessão"""
        state = st.session_state.dashboard_state
        
        if state.date_range:
            start_date, end_date = state.date_range
        else:
            end_date = date.today()
            start_date = end_date - timedelta(days=self.settings.analytics.default_period_days)
        
        return FilterParams(
            start_date=start_date,
            end_date=end_date,
            funds=state.selected_funds if state.selected_funds else None,
            custodians=state.selected_custodians if state.selected_custodians else None,
            limit=self.settings.ui.max_records_display
        )