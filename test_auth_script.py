#!/usr/bin/env python3
"""
Script para testar configuração Microsoft Entra ID
Execute: python test_microsoft_auth.py
"""

import os
import sys
import urllib3
from dotenv import load_dotenv

# Desabilitar warnings SSL para ambientes corporativos
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def test_microsoft_auth_config():
    """Testa configuração Microsoft Entra ID"""
    
    print("🔍 Testando configuração Microsoft Entra ID...\n")
    
    # Carregar variáveis de ambiente
    load_dotenv()
    
    # Verificar variáveis obrigatórias
    required_vars = {
        'MICROSOFT_ENTRA_ENABLED': os.getenv('MICROSOFT_ENTRA_ENABLED'),
        'AZURE_CLIENT_ID': os.getenv('AZURE_CLIENT_ID'),
        'AZURE_CLIENT_SECRET': os.getenv('AZURE_CLIENT_SECRET'),
        'REDIRECT_URI': os.getenv('REDIRECT_URI'),
        'METADATA_URL': os.getenv('METADATA_URL'),
        'COOKIE_SECRET': os.getenv('COOKIE_SECRET')
    }
    
    print("1️⃣ Verificando variáveis de ambiente:")
    missing_vars = []
    
    for var_name, var_value in required_vars.items():
        if var_value:
            # Mascarar secrets
            if 'SECRET' in var_name:
                display_value = f"{var_value[:8]}...{var_value[-4:]}" if len(var_value) > 12 else "***"
            else:
                display_value = var_value
            print(f"   ✅ {var_name}: {display_value}")
        else:
            print(f"   ❌ {var_name}: NÃO DEFINIDA")
            missing_vars.append(var_name)
    
    if missing_vars:
        print(f"\n❌ Variáveis faltando: {', '.join(missing_vars)}")
        return False
    
    # Testar conexão com metadata (com fallback para SSL)
    print("\n2️⃣ Testando conexão com Azure AD:")
    try:
        import requests
        metadata_url = required_vars['METADATA_URL']
        
        # Primeira tentativa com SSL normal
        try:
            http_response = requests.get(metadata_url, timeout=10)
            ssl_note = ""
        except requests.exceptions.SSLError:
            # Segunda tentativa ignorando SSL (ambiente corporativo)
            print("   ⚠️  Problema SSL detectado, tentando com verificação desabilitada...")
            http_response = requests.get(metadata_url, timeout=10, verify=False)
            ssl_note = " (SSL verification disabled - ambiente corporativo)"
        
        if http_response.status_code == 200:
            metadata = http_response.json()
            print(f"   ✅ Metadata URL acessível{ssl_note}")
            print(f"   📋 Issuer: {metadata.get('issuer', 'N/A')}")
            auth_endpoint = metadata.get('authorization_endpoint', 'N/A')
            if len(auth_endpoint) > 50:
                auth_endpoint = auth_endpoint[:50] + "..."
            print(f"   🔗 Authorization endpoint: {auth_endpoint}")
            
            if ssl_note:
                print("   💡 Para produção, configure certificados SSL corporativos")
        else:
            print(f"   ❌ Erro ao acessar metadata: HTTP {http_response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Erro na conexão: {str(e)}")
        print("   💡 Verifique conectividade com internet e proxy corporativo")
        return False
    
    # Verificar redirect URI
    print("\n3️⃣ Verificando Redirect URI:")
    redirect_uri = required_vars['REDIRECT_URI']
    
    if redirect_uri.startswith('https://'):
        print(f"   ✅ Redirect URI seguro: {redirect_uri}")
    elif redirect_uri.startswith('http://localhost'):
        print(f"   ⚠️  Redirect URI local (desenvolvimento): {redirect_uri}")
    else:
        print(f"   ❌ Redirect URI inseguro: {redirect_uri}")
        print("      💡 Use HTTPS em produção!")
    
    # Verificar domínios autorizados
    print("\n4️⃣ Verificando domínios autorizados:")
    authorized_domains = os.getenv('AUTHORIZED_DOMAINS', '')
    
    if authorized_domains:
        domains = [d.strip() for d in authorized_domains.split(',')]
        print(f"   ✅ Domínios configurados: {', '.join(domains)}")
    else:
        print("   ⚠️  Nenhum domínio específico configurado (todos permitidos)")
    
    # Teste de importação
    print("\n5️⃣ Testando importações Python:")
    
    # Streamlit
    try:
        import streamlit
        print(f"   ✅ Streamlit: {streamlit.__version__}")
    except ImportError:
        print("   ❌ Streamlit não instalado")
        print("      💡 Execute: pip install streamlit")
        return False
    
    # Requests
    try:
        import requests
        print(f"   ✅ Requests: {requests.__version__}")
    except ImportError:
        print("   ❌ Requests não instalado")
        print("      💡 Execute: pip install requests")
        return False
    
    # PyJWT
    try:
        import jwt
        print(f"   ✅ PyJWT instalado")
    except ImportError:
        print("   ❌ PyJWT não instalado")
        print("      💡 Execute: pip install PyJWT")
        return False
    
    # streamlit-oauth
    try:
        from streamlit_oauth import OAuth2Component
        print(f"   ✅ streamlit-oauth instalado")
    except ImportError:
        print("   ❌ streamlit-oauth não instalado")
        print("      💡 Execute: pip install streamlit-oauth")
        return False
    
    # cryptography
    try:
        import cryptography
        print(f"   ✅ cryptography: {cryptography.__version__}")
    except ImportError:
        print("   ❌ cryptography não instalado")
        print("      💡 Execute: pip install cryptography")
        return False
    
    # python-dotenv
    try:
        import dotenv
        print(f"   ✅ python-dotenv instalado")
    except ImportError:
        print("   ❌ python-dotenv não instalado")
        print("      💡 Execute: pip install python-dotenv")
        return False
    
    # Teste de configuração da aplicação
    print("\n6️⃣ Testando módulos da aplicação:")
    try:
        # Verificar se estamos no diretório correto
        if not os.path.exists('config'):
            print("   ❌ Diretório 'config' não encontrado")
            print("      💡 Execute o script a partir da raiz do projeto")
            return False
        
        sys.path.append('.')
        from config.entra_config import EntraConfig
        
        config = EntraConfig()
        if config.is_enabled():
            print("   ✅ Configuração Microsoft Entra carregada e habilitada")
            print(f"      📧 Domínios autorizados: {config.authorized_domains or 'Todos'}")
        else:
            print("   ❌ Configuração Microsoft Entra desabilitada ou inválida")
            return False
            
    except ImportError as e:
        print(f"   ❌ Erro ao importar módulos: {e}")
        print("      💡 Verifique se todos os arquivos foram criados corretamente")
        return False
    except Exception as e:
        print(f"   ❌ Erro na configuração: {e}")
        return False
    
    # Teste adicional: verificar estrutura de arquivos
    print("\n7️⃣ Verificando estrutura de arquivos:")
    required_files = [
        'config/entra_config.py',
        'core/microsoft_auth.py', 
        'core/auth_service.py',
        'main.py'
    ]
    
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"   ✅ {file_path}")
        else:
            print(f"   ❌ {file_path} - FALTANDO")
            print(f"      💡 Crie o arquivo {file_path}")
            return False
    
    print("\n🎉 Todos os testes passaram! Configuração Microsoft Entra OK!")
    print("\n📋 Próximos passos:")
    print("   1. Execute: streamlit run main.py")
    print("   2. Teste o login com uma conta Microsoft corporativa")
    print("   3. Verifique se o perfil foi mapeado corretamente")
    
    if ssl_note:
        print("\n⚠️  Nota sobre SSL:")
        print("   - Ambiente corporativo detectado")
        print("   - Em produção, configure certificados SSL adequados")
        print("   - O login Microsoft ainda funcionará corretamente")
    
    return True

def install_dependencies():
    """Instala dependências necessárias"""
    print("📦 Instalando dependências do Microsoft Entra ID...\n")
    
    dependencies = [
        "streamlit-oauth",
        "requests", 
        "PyJWT",
        "cryptography",
        "python-dotenv"
    ]
    
    import subprocess
    
    for dep in dependencies:
        try:
            print(f"   📥 Instalando {dep}...")
            result = subprocess.run([sys.executable, "-m", "pip", "install", dep], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print(f"   ✅ {dep} instalado com sucesso")
            else:
                print(f"   ❌ Erro ao instalar {dep}: {result.stderr}")
        except Exception as e:
            print(f"   ❌ Erro ao instalar {dep}: {e}")
    
    print("\n✅ Instalação concluída!")

def generate_cookie_secret():
    """Gera uma nova chave secreta para cookies"""
    import secrets
    
    print("\n🔑 Gerando nova chave secreta para cookies:")
    secret = secrets.token_hex(32)
    print(f"COOKIE_SECRET={secret}")
    print("\n💡 Adicione esta linha ao seu arquivo .env")

if __name__ == "__main__":
    print("=" * 60)
    print("🔐 TESTE DE CONFIGURAÇÃO MICROSOFT ENTRA ID")
    print("=" * 60)
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--generate-secret":
            generate_cookie_secret()
        elif sys.argv[1] == "--install-deps":
            install_dependencies()
        elif sys.argv[1] == "--help":
            print("Opções disponíveis:")
            print("  --generate-secret    Gera nova chave secreta")
            print("  --install-deps       Instala dependências")
            print("  --help              Mostra esta ajuda")
    else:
        success = test_microsoft_auth_config()
        
        if not success:
            print("\n💡 Dicas:")
            print("   - Execute: python test_auth_script.py --install-deps")
            print("   - Verifique o arquivo .env")
            print("   - Confirme configuração no Azure Portal")
            sys.exit(1)