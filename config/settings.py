import os
import yaml
from dataclasses import dataclass
from typing import Dict, List, Optional
from pathlib import Path

@dataclass
class DatabaseConfig:
    host: str
    port: int
    user: str
    password: str
    database: str
    pool_size: int = 5
    pool_timeout: int = 30

@dataclass
class SecurityConfig:
    secret_key: str
    session_timeout: int = 480
    max_login_attempts: int = 5
    
@dataclass
class AnalyticsConfig:
    liquidity_ratio_min: float = 0.8
    liquidity_ratio_max: float = 1.5
    concentration_threshold: float = 30.0
    default_period_days: int = 45
    cache_ttl: int = 1800

@dataclass
class UIConfig:
    refresh_interval: int = 300
    max_records_display: int = 10000

class AppSettings:
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self._get_default_config_path()
        self._load_config()
    
    def _get_default_config_path(self) -> str:
        return str(Path(__file__).parent / "app_config.yaml")
    
    def _load_config(self):
        # Carregar configuração do arquivo YAML se existir
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
        else:
            config_data = {}
        
        # Database config
        db_config = config_data.get('database', {})
        self.database = DatabaseConfig(
            host=os.getenv('DB_HOST', db_config.get('host', 'localhost')),
            port=int(os.getenv('DB_PORT', db_config.get('port', 3306))),
            user=os.getenv('DB_USER', db_config.get('user', 'user')),
            password=os.getenv('DB_PASSWORD', db_config.get('password', 'password')),
            database=os.getenv('DB_NAME', db_config.get('database', 'funds_db')),
            pool_size=int(os.getenv('DB_POOL_SIZE', db_config.get('pool_size', 5))),
            pool_timeout=int(os.getenv('DB_POOL_TIMEOUT', db_config.get('pool_timeout', 30)))
        )
        
        # Security config
        security_config = config_data.get('security', {})
        self.security = SecurityConfig(
            secret_key=os.getenv('SECRET_KEY', security_config.get('secret_key', 'default-key')),
            session_timeout=int(os.getenv('SESSION_TIMEOUT', security_config.get('session_timeout', 480))),
            max_login_attempts=int(os.getenv('MAX_LOGIN_ATTEMPTS', security_config.get('max_login_attempts', 5)))
        )
        
        # Analytics config
        analytics_config = config_data.get('analytics', {})
        self.analytics = AnalyticsConfig(
            liquidity_ratio_min=float(analytics_config.get('liquidity_ratio_min', 0.8)),
            liquidity_ratio_max=float(analytics_config.get('liquidity_ratio_max', 1.5)),
            concentration_threshold=float(analytics_config.get('concentration_threshold', 30.0)),
            default_period_days=int(analytics_config.get('default_period_days', 45)),
            cache_ttl=int(analytics_config.get('cache_ttl', 1800))
        )
        
        # UI config
        ui_config = config_data.get('ui', {})
        self.ui = UIConfig(
            refresh_interval=int(ui_config.get('refresh_interval', 300)),
            max_records_display=int(ui_config.get('max_records_display', 10000))
        )
        
        # Load rules
        self.rules = self._load_rules()
    
    def _load_rules(self) -> Dict:
        """Carrega regras de análise de arquivos YAML"""
        rules_path = Path(__file__).parent / "rules"
        rules = {}
        
        if rules_path.exists():
            for rule_file in rules_path.glob("*.yaml"):
                with open(rule_file, 'r', encoding='utf-8') as f:
                    rule_data = yaml.safe_load(f)
                    rules[rule_file.stem] = rule_data
        
        return rules