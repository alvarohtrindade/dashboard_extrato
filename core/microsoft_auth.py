import streamlit as st
from streamlit_oauth import OAuth2Component
import requests
import jwt
from typing import Optional, Dict, Any
import logging
from datetime import datetime

from config.entra_config import EntraConfig
from core.models import User

logger = logging.getLogger(__name__)

class MicrosoftEntraAuth:
    """Gerenciador de autenticação Microsoft Entra ID"""
    
    def __init__(self, entra_config: EntraConfig):
        self.config = entra_config
        self.oauth2 = None
        
        if self.config.is_enabled():
            self._init_oauth2()
    
    def _init_oauth2(self):
        """Inicializa componente OAuth2"""
        try:
            # Configuração OAuth2 para Microsoft
            authorize_url = "https://login.microsoftonline.com/organizations/oauth2/v2.0/authorize"
            token_url = "https://login.microsoftonline.com/organizations/oauth2/v2.0/token"
            refresh_token_url = token_url
            revoke_token_url = "https://login.microsoftonline.com/organizations/oauth2/v2.0/logout"
            
            self.oauth2 = OAuth2Component(
                client_id=self.config.client_id,
                client_secret=self.config.client_secret,
                authorize_endpoint=authorize_url,
                token_endpoint=token_url,
                refresh_token_endpoint=refresh_token_url,
                revoke_token_endpoint=revoke_token_url
            )
            
            logger.info("Microsoft OAuth2 inicializado com sucesso")
            
        except Exception as e:
            logger.error(f"Erro ao inicializar OAuth2: {e}")
            self.oauth2 = None
    
    def is_available(self) -> bool:
        """Verifica se a autenticação Microsoft está disponível"""
        return self.config.is_enabled() and self.oauth2 is not None
    
    def render_login_button(self) -> Optional[str]:
        """Renderiza botão de login Microsoft e retorna token se autenticado"""
        if not self.is_available():
            return None
        
        try:
            # Scopes necessários para obter informações do usuário
            scopes = [
                "openid",
                "profile", 
                "email",
                "User.Read"
            ]
            
            # Renderizar componente OAuth2
            result = self.oauth2.authorize_button(
                name="Login com Microsoft",
                icon="https://upload.wikimedia.org/wikipedia/commons/4/44/Microsoft_logo.svg",
                redirect_uri=self.config.redirect_uri,
                scope=" ".join(scopes),
                key="microsoft_oauth",
                use_container_width=True
            )
            
            if result and 'token' in result:
                return result['token']
            
            return None
            
        except Exception as e:
            logger.error(f"Erro no login Microsoft: {e}")
            st.error("Erro ao processar login Microsoft. Tente novamente.")
            return None
    
    def get_user_info(self, access_token: str) -> Optional[Dict[str, Any]]:
        """Obtém informações do usuário usando o token de acesso"""
        try:
            # Chamar Microsoft Graph API
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(
                'https://graph.microsoft.com/v1.0/me',
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                user_info = response.json()
                logger.info(f"Informações do usuário obtidas: {user_info.get('userPrincipalName', 'unknown')}")
                return user_info
            else:
                logger.error(f"Erro ao obter informações do usuário: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Erro ao chamar Microsoft Graph: {e}")
            return None
    
    def create_user_from_microsoft(self, user_info: Dict[str, Any]) -> Optional[User]:
        """Cria objeto User a partir das informações do Microsoft"""
        try:
            # Validar domínio se configurado
            email = user_info.get('mail') or user_info.get('userPrincipalName', '')
            if self.config.authorized_domains:
                email_domain = email.split('@')[1] if '@' in email else ''
                if email_domain not in self.config.authorized_domains:
                    logger.warning(f"Domínio não autorizado: {email_domain}")
                    return None
            
            # Determinar perfil baseado em informações do usuário
            profile = self._determine_user_profile(user_info)
            
            # Criar objeto User
            user = User(
                id=hash(user_info.get('id', '')),  # Usar hash do ID Microsoft
                username=user_info.get('userPrincipalName', ''),
                email=email,
                full_name=user_info.get('displayName', ''),
                profile=profile,
                active=True,
                provider='microsoft',
                last_login=datetime.now()
            )
            
            logger.info(f"Usuário Microsoft criado: {user.email} - Perfil: {user.profile}")
            return user
            
        except Exception as e:
            logger.error(f"Erro ao criar usuário Microsoft: {e}")
            return None
    
    def _determine_user_profile(self, user_info: Dict[str, Any]) -> str:
        """Determina o perfil do usuário baseado nas informações"""
        try:
            # Verificar se é admin baseado no email ou outros critérios
            email = user_info.get('mail') or user_info.get('userPrincipalName', '')
            display_name = user_info.get('displayName', '').lower()
            job_title = user_info.get('jobTitle', '').lower()
            
            # Lógica de mapeamento de perfis
            if any(term in email.lower() for term in ['admin', 'administrator']):
                return 'admin'
            elif any(term in display_name for term in ['admin', 'administrator']):
                return 'admin'
            elif any(term in job_title for term in ['diretor', 'director', 'gerente', 'manager']):
                return 'gestor'
            elif any(term in job_title for term in ['analista', 'analyst']):
                return 'analista'
            else:
                return 'viewer'  # Perfil padrão
                
        except Exception as e:
            logger.error(f"Erro ao determinar perfil: {e}")
            return 'viewer'
    
    def logout(self):
        """Limpa dados de autenticação"""
        try:
            # Limpar cookies e sessão
            if 'microsoft_user' in st.session_state:
                del st.session_state['microsoft_user']
            
            # Limpar cache OAuth2
            if hasattr(st.session_state, 'microsoft_oauth'):
                del st.session_state['microsoft_oauth']
            
            logger.info("Logout Microsoft realizado")
            
        except Exception as e:
            logger.error(f"Erro no logout: {e}")