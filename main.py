import streamlit as st
import logging
from pathlib import Path

from config.settings import AppSettings
from core.auth_service import AuthService
from core.analytics_engine import AnalyticsEngine
from data.repository import DataRepository
from ui.dashboard import Dashboard
from ui.components import UIComponents

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Ponto de entrada da aplicação"""
    st.set_page_config(
        page_title="Painel Catálise - Extratos",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Inicializar serviços
    settings = AppSettings()
    repository = DataRepository(settings.database)
    auth_service = AuthService(repository, settings.security)
    analytics_engine = AnalyticsEngine(settings.analytics)
    
    # Aplicar estilos
    UIComponents.apply_global_styles()
    
    # Inicializar dashboard
    dashboard = Dashboard(
        auth_service=auth_service,
        repository=repository,
        analytics_engine=analytics_engine,
        settings=settings
    )
    
    # Executar aplicação
    dashboard.run()

if __name__ == "__main__":
    main()