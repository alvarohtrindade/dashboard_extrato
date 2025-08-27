import os
import streamlit as st
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class EntraConfig:
    """Configurações do Microsoft Entra ID"""
    
    def __init__(self):
        self.enabled = os.getenv('MICROSOFT_ENTRA_ENABLED', 'false').lower() == 'true'
        self.client_id = os.getenv('AZURE_CLIENT_ID', '')
        self.client_secret = os.getenv('AZURE_CLIENT_SECRET', '')
        self.redirect_uri = os.getenv('REDIRECT_URI', 'https://analytics.cataliseinvestimentos.com/auth')
        self.metadata_url = os.getenv('METADATA_URL', '')
        self.authorized_domains = os.getenv('AUTHORIZED_DOMAINS', '').split(',') if os.getenv('AUTHORIZED_DOMAINS') else []
        self.cookie_secret = os.getenv('COOKIE_SECRET', '')
        
        # Validar configuração
        self._validate_config()
    
    def _validate_config(self):
        """Valida se a configuração está completa"""
        if not self.enabled:
            return
        
        required_fields = {
            'AZURE_CLIENT_ID': self.client_id,
            'AZURE_CLIENT_SECRET': self.client_secret,
            'REDIRECT_URI': self.redirect_uri,
            'METADATA_URL': self.metadata_url,
            'COOKIE_SECRET': self.cookie_secret
        }
        
        missing_fields = [field for field, value in required_fields.items() if not value]
        
        if missing_fields:
            logger.error(f"Microsoft Entra configuração incompleta. Campos faltando: {missing_fields}")
            self.enabled = False
        else:
            logger.info("Microsoft Entra configurado corretamente")
    
    def is_enabled(self) -> bool:
        """Verifica se o Microsoft Entra está habilitado e configurado"""
        return self.enabled
    
    def get_config_dict(self) -> Dict[str, Any]:
        """Retorna configuração como dicionário para o streamlit-authenticator"""
        if not self.enabled:
            return {}
        
        return {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'redirect_uri': self.redirect_uri,
            'metadata_url': self.metadata_url,
            'cookie_secret': self.cookie_secret,
            'authorized_domains': self.authorized_domains
        }