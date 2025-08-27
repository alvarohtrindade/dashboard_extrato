# 🔐 Guia de Segurança - Dashboard Catálise

## ⚠️ IMPORTANTE: Vulnerabilidades Corrigidas

Durante a revisão de segurança, as seguintes vulnerabilidades críticas foram identificadas e **CORRIGIDAS**:

### 🚨 Críticas (Corrigidas)
- [x] **Credenciais hardcoded** removidas de `config/app_config.yaml`
- [x] **Secret keys expostas** substituídas por variáveis de ambiente
- [x] **Passwords em plaintext** migrados para hash bcrypt
- [x] **SQL Injection** prevenido com queries parametrizadas

### ⚡ Melhorias Implementadas
- [x] **Rate Limiting** em tentativas de login
- [x] **Session Timeout** configurável
- [x] **Sanitização de logs** - credenciais nunca logadas
- [x] **.gitignore** robusto para prevenir commits acidentais

## 🛡️ Configuração Segura

### 1. Variáveis de Ambiente (Obrigatório)

```bash
# .env (nunca comitar)
DB_HOST=seu-host-aurora.amazonaws.com
DB_USER=dashboard_user
DB_PASSWORD=senha-super-segura-aqui
DB_NAME=DW_STAGING

# Chave para sessions (gerar nova)
SECRET_KEY=sua-chave-aleatoria-de-32-chars

# Microsoft Authentication (opcional)
AZURE_CLIENT_ID=seu-client-id
AZURE_CLIENT_SECRET=seu-client-secret
AZURE_TENANT_ID=seu-tenant-id
```

### 2. Streamlit Cloud Secrets

Configure no painel do Streamlit Cloud:

```toml
[database]
DB_HOST = "seu-host.amazonaws.com"
DB_USER = "dashboard_user"
DB_PASSWORD = "senha-segura"

[security]
SECRET_KEY = "chave-producao-64-chars"
```

## 🔒 Checklist de Segurança

### Deploy em Produção
- [ ] ✅ Todas as credenciais em secrets/env vars
- [ ] ✅ HTTPS habilitado
- [ ] ✅ Firewall de banco configurado (apenas IPs autorizados)
- [ ] ✅ Rate limiting ativo
- [ ] ✅ Logs não contêm credenciais
- [ ] ✅ Backup de configurações seguras

### Autenticação
- [ ] ✅ Senhas com hash bcrypt
- [ ] ✅ Sessions com timeout
- [ ] ✅ Rate limiting (5 tentativas/15min)
- [ ] ✅ Logout seguro limpa sessão

### Banco de Dados
- [ ] ✅ Queries parametrizadas (previne SQL injection)
- [ ] ✅ Pool de conexões limitado
- [ ] ✅ Timeout de conexão configurado
- [ ] ✅ User com privilégios mínimos necessários

### Código
- [ ] ✅ Não há print() com dados sensíveis
- [ ] ✅ Logs estruturados sem credenciais
- [ ] ✅ Validação de entrada robusta
- [ ] ✅ Error handling não expõe detalhes internos

## 🚨 Resposta a Incidentes

### Se Credenciais Vazaram:
1. **Rotacionar imediatamente** todas as senhas/chaves
2. **Auditoria de logs** para identificar acesso não autorizado
3. **Notificar stakeholders** sobre o incidente
4. **Revisar permissões** de usuários e sistemas

### Se Acesso Não Autorizado:
1. **Desabilitar usuário comprometido**
2. **Forçar logout** de todas as sessões
3. **Análise de logs** de atividade suspeita
4. **Relatório de segurança** para gestão

## 🔧 Comandos Úteis

### Gerar Nova Chave Secreta:
```python
import secrets
print(f"SECRET_KEY={secrets.token_hex(32)}")
```

### Testar Conectividade Segura:
```bash
# Testar sem expor credenciais
python -c "
from utils.mysql_connector_utils import get_mysql_connector
connector = get_mysql_connector()
print('✅ Conexão OK' if connector.test_connection() else '❌ Falha')
"
```

### Verificar Configuração:
```bash
# Listar variáveis (sem valores)
python -c "
import os
vars_expected = ['DB_HOST', 'DB_USER', 'DB_PASSWORD', 'SECRET_KEY']
missing = [v for v in vars_expected if not os.getenv(v)]
print('❌ Faltando:', missing) if missing else print('✅ Variáveis OK')
"
```

## 📞 Contatos de Segurança

- **Time de DevOps**: Para questões de infraestrutura
- **Time de Dados**: Para questões de acesso aos dados
- **Compliance**: Para questões regulatórias

---

**⚡ Desenvolvido seguindo OWASP Top 10 e práticas do CLAUDE.md**