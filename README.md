# Dashboard Catálise - Extratos Financeiros

## 🚀 Deploy em Produção

Dashboard profissional para análise de extratos financeiros de fundos de investimento, com foco em liquidez, compliance e performance.

### ✨ Recursos Principais

- **📊 KPIs Financeiros em Tempo Real**: Liquidez, concentração, eficiência operacional
- **🔍 Filtros Avançados**: Busca dinâmica de fundos, períodos personalizados
- **💡 Cache Inteligente**: Performance otimizada para grandes volumes
- **🔐 Autenticação Segura**: Microsoft Entra ID + login tradicional
- **📈 Análises Críticas**: Alertas de risco e métricas de compliance

## 🏗️ Estrutura do Projeto

```
catalise-dashboard/
├── config/
│   ├── app_config.yaml          # Configurações principais
│   ├── settings.py              # Classes de configuração
│   └── rules/
│       └── liquidity_analysis.yaml  # Regras de análise
├── core/
│   ├── analytics_engine.py      # Motor de análises
│   ├── auth_service.py          # Autenticação
│   └── models.py               # Modelos de dados
├── data/
│   ├── database.py             # Gerenciador de banco
│   ├── queries.py              # Builder de queries
│   └── repository.py           # Camada de dados
├── ui/
│   ├── charts.py               # Gráficos
│   ├── components.py           # Componentes UI
│   ├── dashboard.py            # Interface principal
│   └── filters.py              # Filtros
├── main.py                     # Ponto de entrada
└── requirements.txt            # Dependências
```

## 🚀 Instalação e Configuração

### 1. Instalar Dependências

```bash
pip install streamlit pandas plotly mysql-connector-python sqlalchemy pyyaml bcrypt
```

### 2. Configurar Banco de Dados

Edite `config/app_config.yaml`:

```yaml
database:
  host: "seu-host"
  port: 3306
  user: "seu-usuario"
  password: "sua-senha"
  database: "sua-base"
```

### 3. Executar Aplicação

```bash
streamlit run main.py
```

## 📊 Funcionalidades

### Extratos
- Visualização de dados da view `DW_STAGING.vw_extrato`
- Filtros por período, custodiante e fundos
- Métricas automáticas de créditos/débitos

### Análises
- **Liquidez**: Razão entrada/saída, alertas automáticos
- **Concentração**: Análise de distribuição por fundo
- **Evolução**: Tendências de saldo histórico

### Monitoramento
- Logs de acesso (apenas admin/gestor)
- Alertas de compliance
- Métricas de sistema

## ⚙️ Configuração Avançada

### Regras de Análise

Crie arquivos YAML em `config/rules/` para definir:

```yaml
# exemplo: liquidez_personalizada.yaml
thresholds:
  liquidity_ratio:
    critical_low: 0.4
    warning_low: 0.7
```

### Mapeamento de Campos

Configure em `app_config.yaml`:

```yaml
field_mapping:
  value_calculation: "COALESCE(entrada, 0) - COALESCE(saida, 0)"
  operation_type_logic: |
    CASE 
      WHEN entrada > 0 THEN 'Crédito'
      WHEN saida > 0 THEN 'Débito'
    END
```

## 🔧 Manutenção

### Adicionar Nova Análise

1. **Criar regra YAML** em `config/rules/`:
```yaml
name: "Minha Análise"
queries:
  main_query: |
    SELECT nmfundo, SUM(valor) as total
    FROM DW_STAGING.vw_extrato
    WHERE {filtros}
```

2. **Implementar no Analytics Engine**:
```python
def analyze_custom(self, repository, filters):
    # Lógica da análise
    return AnalysisResult(...)
```

3. **Adicionar à UI** em `ui/dashboard.py`

### Modificar Queries

Todas as queries estão em `data/queries.py`. Para alterar:

```python
def build_custom_query(self, filters):
    return """
    SELECT campo1, campo2
    FROM DW_STAGING.vw_extrato
    WHERE condicoes
    """
```

### Ajustar Thresholds

Edite `config/app_config.yaml`:

```yaml
analytics:
  liquidity_ratio_min: 0.8    # Novo limite
  concentration_threshold: 25.0
```

## 📈 Monitoramento

### Performance
- Queries são automaticamente cacheadas
- TTL configurável por análise
- Pool de conexões otimizado

### Logs
```python
import logging
logger = logging.getLogger(__name__)
logger.info("Evento importante")
```

### Métricas
- Tempo de resposta das queries
- Taxa de cache hit
- Número de usuários ativos

## 🔐 Segurança

### Usuários Demo
- admin/admin123 (acesso total)
- gestor/gestor123 (análises)
- usuario/usuario123 (visualização)

### Produção
Implemente autenticação real em `core/auth_service.py`:

```python
def authenticate(self, username, password):
    # Conectar com AD/LDAP/OAuth
    pass
```

## 🚨 Troubleshooting

### Conexão com Banco
```bash
# Testar conectividade
python -c "from data.repository import DataRepository; print(DataRepository().is_connected())"
```

### Cache Limpo
```python
# No Streamlit
st.cache_data.clear()
```

### Logs Detalhados
```python
# Em config/settings.py
logging.basicConfig(level=logging.DEBUG)
```

## 📋 Checklist de Deploy

- [ ] Configurar variáveis de ambiente
- [ ] Testar conexão com banco
- [ ] Validar permissões de usuário
- [ ] Configurar SSL/TLS
- [ ] Monitorar performance
- [ ] Backup das configurações

## 🔄 Atualizações

### Versioning
- Configurações: `config/app_config.yaml`
- Regras: `config/rules/*.yaml`
- Código: Git tags

### Rollback
1. Backup da configuração atual
2. Restaurar versão anterior
3. Limpar cache
4. Reiniciar aplicação

## 📞 Suporte

Para dúvidas sobre:
- **Configuração**: Verificar `app_config.yaml`
- **Queries**: Consultar `data/queries.py`
- **Análises**: Revisar `config/rules/`
- **UI**: Modificar `ui/components.py`

---