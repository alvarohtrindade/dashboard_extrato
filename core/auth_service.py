import bcrypt
import logging
from typing import Optional

from data.repository import DataRepository
from config.settings import SecurityConfig
from config.entra_config import EntraConfig
from core.models import User
from core.microsoft_auth import MicrosoftEntraAuth

logger = logging.getLogger(__name__)

class AuthService:
    def __init__(self, repository: DataRepository, config: SecurityConfig):
        self.repository = repository
        self.config = config
        
        # Inicializar Microsoft Entra se configurado
        self.entra_config = EntraConfig()
        self.microsoft_auth = MicrosoftEntraAuth(self.entra_config)
    
    def is_microsoft_enabled(self) -> bool:
        """Verifica se autenticação Microsoft está habilitada"""
        return self.microsoft_auth.is_available()
    
    def authenticate_microsoft(self) -> Optional[User]:
        """Autentica usuário via Microsoft Entra"""
        if not self.is_microsoft_enabled():
            return None
        
        try:
            # Renderizar botão e obter token
            access_token = self.microsoft_auth.render_login_button()
            
            if access_token:
                # Obter informações do usuário
                user_info = self.microsoft_auth.get_user_info(access_token)
                
                if user_info:
                    # Criar usuário a partir das informações Microsoft
                    user = self.microsoft_auth.create_user_from_microsoft(user_info)
                    
                    if user:
                        # Salvar na sessão
                        self._save_microsoft_user_session(user, user_info)
                        return user
            
            return None
            
        except Exception as e:
            logger.error(f"Erro na autenticação Microsoft: {e}")
            return None
    
    def authenticate(self, username: str, password: str) -> Optional[User]:
        """Autentica usuário (método legado para fallback)"""
        try:
            if not self.repository.is_connected():
                return self._authenticate_demo_user(username, password)
            
            # TODO: Implementar autenticação com banco
            # Por ora, usar demo users
            return self._authenticate_demo_user(username, password)
            
        except Exception as e:
            logger.error(f"Erro na autenticação: {e}")
            return None
    
    def logout(self):
        """Realiza logout do usuário"""
        try:
            # Logout Microsoft se aplicável
            if self.is_microsoft_enabled():
                self.microsoft_auth.logout()
            
            # Limpar outras sessões
            self._clear_all_sessions()
            
        except Exception as e:
            logger.error(f"Erro no logout: {e}")
    
    def _save_microsoft_user_session(self, user: User, user_info: dict):
        """Salva informações do usuário Microsoft na sessão"""
        import streamlit as st
        st.session_state['microsoft_user'] = user
        st.session_state['microsoft_user_info'] = user_info
        st.session_state['auth_provider'] = 'microsoft'
    
    def _clear_all_sessions(self):
        """Limpa todas as sessões de autenticação"""
        import streamlit as st
        keys_to_clear = [
            'microsoft_user', 
            'microsoft_user_info', 
            'auth_provider',
            'authenticated',
            'current_user'
        ]
        
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
    
    def _authenticate_demo_user(self, username: str, password: str) -> Optional[User]:
        """Autentica usuário demo quando não há conexão com banco"""
        demo_users = {
            'admin': {
                'password': 'admin123',
                'user': User(
                    id=1,
                    username='admin',
                    email='admin@demo.com',
                    full_name='Administrador Demo',
                    profile='admin',
                    active=True,
                    provider='demo'
                )
            },
            'gestor': {
                'password': 'gestor123',
                'user': User(
                    id=2,
                    username='gestor',
                    email='gestor@demo.com',
                    full_name='Gestor Demo',
                    profile='gestor',
                    active=True,
                    provider='demo'
                )
            },
            'usuario': {
                'password': 'usuario123',
                'user': User(
                    id=3,
                    username='usuario',
                    email='usuario@demo.com',
                    full_name='Usuário Demo',
                    profile='viewer',
                    active=True,
                    provider='demo'
                )
            }
        }
        
        if username in demo_users and demo_users[username]['password'] == password:
            logger.info(f"Login demo realizado para usuário: {username}")
            return demo_users[username]['user']
        
        return None
    
    def _hash_password(self, password: str) -> str:
        """Gera hash bcrypt da senha"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def _verify_password(self, password: str, hashed: str) -> bool:
        """Verifica senha contra hash bcrypt"""
        try:
            return bcrypt.checkpw(password.encode(), hashed.encode())
        except Exception as e:
            logger.error(f"Erro ao verificar senha: {e}")
            return False