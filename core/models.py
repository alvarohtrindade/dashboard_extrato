from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from datetime import datetime

@dataclass
class Metric:
    name: str
    value: float
    status: str
    severity: str  # info, warning, critical
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'value': self.value,
            'status': self.status,
            'severity': self.severity,
            'metadata': self.metadata or {}
        }

@dataclass
class Alert:
    type: str
    severity: str
    fund: str
    message: str
    value: float
    timestamp: datetime = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'type': self.type,
            'severity': self.severity,
            'fund': self.fund,
            'message': self.message,
            'value': self.value,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata or {}
        }

@dataclass
class AnalysisResult:
    analysis_type: str
    success: bool
    metrics: Optional[Dict[str, Metric]] = None
    alerts: Optional[List[Alert]] = None
    data: Optional[Dict[str, Any]] = None
    summary: Optional[str] = None
    message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'analysis_type': self.analysis_type,
            'success': self.success,
            'metrics': {k: v.to_dict() for k, v in (self.metrics or {}).items()},
            'alerts': [a.to_dict() for a in (self.alerts or [])],
            'data': self.data,
            'summary': self.summary,
            'message': self.message
        }
    
    def get_critical_alerts(self) -> List[Alert]:
        """Retorna apenas alertas críticos"""
        return [alert for alert in (self.alerts or []) if alert.severity == 'critical']
    
    def get_warning_alerts(self) -> List[Alert]:
        """Retorna apenas alertas de warning"""
        return [alert for alert in (self.alerts or []) if alert.severity == 'warning']
    
    def has_issues(self) -> bool:
        """Verifica se há problemas detectados"""
        return bool(self.alerts and any(a.severity in ['warning', 'critical'] for a in self.alerts))

@dataclass
class User:
    id: int
    username: str
    email: str
    full_name: str
    profile: str
    active: bool
    provider: str = 'local'
    session_id: Optional[str] = None
    last_login: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'profile': self.profile,
            'active': self.active,
            'provider': self.provider,
            'session_id': self.session_id,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }
    
    def has_permission(self, required_profiles: List[str]) -> bool:
        """Verifica se o usuário tem permissão baseada no perfil"""
        return self.profile in required_profiles

@dataclass
class DashboardState:
    authenticated: bool = False
    current_user: Optional[User] = None
    selected_funds: List[str] = None
    selected_custodians: List[str] = None
    date_range: tuple = None
    
    def __post_init__(self):
        if self.selected_funds is None:
            self.selected_funds = []
        if self.selected_custodians is None:
            self.selected_custodians = []