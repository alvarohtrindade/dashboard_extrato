"""
Sistema de autenticação básica e segura para dashboard
Compatível com Streamlit Cloud deployment
"""
import streamlit as st
import hashlib
import secrets
import time
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import bcrypt

from .logging_utils import Log

logger = Log.get_logger(__name__)

class SimpleAuthenticator:
    """Autenticador simples e seguro para dashboard"""
    
    def __init__(self):
        self.max_attempts = 5
        self.lockout_time = 900  # 15 minutos
        self._init_session_state()
    
    def _init_session_state(self):
        """Inicializa estado de sessão para autenticação"""
        if 'auth_attempts' not in st.session_state:
            st.session_state.auth_attempts = {}
        if 'authenticated' not in st.session_state:
            st.session_state.authenticated = False
        if 'user_data' not in st.session_state:
            st.session_state.user_data = None
        if 'session_start' not in st.session_state:
            st.session_state.session_start = None
    
    def _hash_password(self, password: str) -> str:
        """Cria hash seguro da senha"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def _check_password(self, password: str, hashed: str) -> bool:
        """Verifica senha contra hash"""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
        except Exception as e:
            logger.error(f"Erro ao verificar senha: {str(e)}")
            return False
    
    def _get_user_credentials(self) -> Dict[str, Dict[str, str]]:
        """Obtém credenciais de usuário (produção: usar banco de dados)"""
        try:
            # Tentar carregar do Streamlit secrets
            secrets_auth = st.secrets.get('authentication', {})
            if secrets_auth:
                return secrets_auth
        except:
            pass
        
        # Fallback para credenciais demo
        demo_users = {
            "admin": {
                "password": self._hash_password("admin123"),
                "role": "admin",
                "name": "Administrador",
                "permissions": ["read", "write", "admin"]
            },
            "gestor": {
                "password": self._hash_password("gestor123"),
                "role": "manager",
                "name": "Gestor",
                "permissions": ["read", "write"]
            },
            "analista": {
                "password": self._hash_password("analista123"),
                "role": "analyst",
                "name": "Analista",
                "permissions": ["read"]
            }
        }
        
        logger.warning("Usando credenciais demo - não usar em produção!")
        return demo_users
    
    def _check_rate_limit(self, username: str) -> bool:
        """Verifica rate limiting por usuário"""
        now = time.time()
        
        if username in st.session_state.auth_attempts:
            attempts_data = st.session_state.auth_attempts[username]
            
            # Reset attempts se passou tempo de lockout
            if now - attempts_data.get('last_attempt', 0) > self.lockout_time:
                st.session_state.auth_attempts[username] = {'count': 0, 'last_attempt': now}
                return True
            
            # Verificar se excedeu tentativas
            if attempts_data.get('count', 0) >= self.max_attempts:
                remaining_time = self.lockout_time - (now - attempts_data.get('last_attempt', 0))
                if remaining_time > 0:
                    logger.warning(f"Rate limit atingido para {username}: {remaining_time:.0f}s restantes")
                    return False
        
        return True
    
    def _record_attempt(self, username: str, success: bool):
        """Registra tentativa de login"""
        now = time.time()
        
        if username not in st.session_state.auth_attempts:
            st.session_state.auth_attempts[username] = {'count': 0, 'last_attempt': now}
        
        if success:
            # Reset counter em sucesso
            st.session_state.auth_attempts[username] = {'count': 0, 'last_attempt': now}
            logger.info(f"Login bem-sucedido: {username}")
        else:
            # Incrementar contador de falhas
            st.session_state.auth_attempts[username]['count'] += 1
            st.session_state.auth_attempts[username]['last_attempt'] = now
            logger.warning(f"Login falhou para {username}: tentativa {st.session_state.auth_attempts[username]['count']}")
    
    def authenticate(self, username: str, password: str) -> bool:
        """Autentica usuário com rate limiting"""
        if not username or not password:
            return False
        
        # Verificar rate limiting
        if not self._check_rate_limit(username):
            attempts_data = st.session_state.auth_attempts.get(username, {})
            remaining_time = self.lockout_time - (time.time() - attempts_data.get('last_attempt', 0))
            st.error(f"⏳ Muitas tentativas falharam. Tente novamente em {remaining_time/60:.1f} minutos")
            return False
        
        # Carregar credenciais
        users = self._get_user_credentials()
        
        if username in users:
            user_data = users[username]
            
            # Verificar senha
            if self._check_password(password, user_data['password']):
                # Login bem-sucedido
                self._record_attempt(username, True)
                
                # Definir dados de sessão
                st.session_state.authenticated = True
                st.session_state.user_data = {
                    'username': username,
                    'role': user_data.get('role', 'user'),
                    'name': user_data.get('name', username.title()),
                    'permissions': user_data.get('permissions', ['read']),
                    'login_time': datetime.now()
                }
                st.session_state.session_start = time.time()
                
                logger.info(f"Login realizado: {username} ({user_data.get('role', 'user')})")
                return True
            else:
                self._record_attempt(username, False)
        else:
            self._record_attempt(username, False)
        
        return False
    
    def logout(self):
        """Realiza logout do usuário"""
        if st.session_state.get('user_data'):
            username = st.session_state.user_data.get('username', 'unknown')
            logger.info(f"Logout realizado: {username}")
        
        # Limpar estado de sessão
        st.session_state.authenticated = False
        st.session_state.user_data = None
        st.session_state.session_start = None
    
    def is_authenticated(self) -> bool:
        """Verifica se usuário está autenticado"""
        return st.session_state.get('authenticated', False)
    
    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """Obtém dados do usuário atual"""
        return st.session_state.get('user_data')
    
    def has_permission(self, permission: str) -> bool:
        """Verifica se usuário tem permissão específica"""
        user_data = self.get_current_user()
        if not user_data:
            return False
        
        permissions = user_data.get('permissions', [])
        return permission in permissions
    
    def check_session_timeout(self, timeout_minutes: int = 60):
        """Verifica timeout de sessão"""
        if not self.is_authenticated():
            return
        
        session_start = st.session_state.get('session_start')
        if session_start:
            elapsed = time.time() - session_start
            if elapsed > (timeout_minutes * 60):
                logger.info("Sessão expirada por timeout")
                self.logout()
                st.error("⏰ Sessão expirada. Faça login novamente.")
                st.rerun()
    
    def render_login_form(self) -> bool:
        """Renderiza formulário de login"""
        st.markdown("""
        <div style='background: white; padding: 2rem; border-radius: 12px; 
                    box-shadow: 0 4px 20px rgba(0,0,0,0.1); margin: 2rem 0;'>
            <h2 style='text-align: center; color: #1E3A8A; margin-bottom: 2rem;'>
                🔐 Login Dashboard Catálise
            </h2>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("login_form", clear_on_submit=True):
            username = st.text_input("👤 Usuário", placeholder="Digite seu usuário")
            password = st.text_input("🔒 Senha", type="password", placeholder="Digite sua senha")
            
            col1, col2 = st.columns(2)
            with col1:
                login_btn = st.form_submit_button("🚀 Entrar", type="primary", use_container_width=True)
            with col2:
                demo_btn = st.form_submit_button("📋 Credenciais Demo", use_container_width=True)
            
            if demo_btn:
                st.info("""
                **👤 Usuários Demo:**
                - `admin` / `admin123` - Acesso total
                - `gestor` / `gestor123` - Gestão e análises  
                - `analista` / `analista123` - Somente leitura
                """)
            
            if login_btn and username and password:
                if self.authenticate(username, password):
                    st.success("✅ Login realizado com sucesso!")
                    st.rerun()
                else:
                    st.error("❌ Credenciais inválidas!")
                    return False
        
        return False
    
    def render_user_info(self):
        """Renderiza informações do usuário logado"""
        user_data = self.get_current_user()
        if user_data:
            with st.sidebar:
                st.markdown(f"""
                **👤 {user_data['name']}**
                
                - **Perfil:** {user_data['role'].title()}
                - **Login:** {user_data['login_time'].strftime('%H:%M')}
                """)
                
                if st.button("🚪 Sair", use_container_width=True):
                    self.logout()
                    st.rerun()

# Instância global
authenticator = SimpleAuthenticator()