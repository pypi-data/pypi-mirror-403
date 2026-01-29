"""
Sistema de configuração para a API Nibo
"""
import os
import warnings
from pathlib import Path
from typing import Optional, Dict

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.backends import default_backend
    import base64
    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False

import json


class NiboSettings:
    """Gerencia as configurações da API Nibo usando settings.json"""
    
    def __init__(self, tokens_path: Optional[str] = None):
        """
        Inicializa a configuração
        
        Args:
            tokens_path: Caminho para o arquivo tokens.json (opcional). Se None, tenta
                        usar NIBO_TOKENS_FILE ou tokens_path do settings.json.
        """
        # Carrega configurações do settings.json
        self._settings_data = self._load_settings_json()
        
        # Carrega tokens de arquivo separado se especificado
        if tokens_path is None:
            tokens_path = self._get_tokens_path()
        
        if tokens_path:
            self.tokens_path = Path(tokens_path)
            self._tokens_config = self._load_tokens_config()
        else:
            self.tokens_path = None
            self._tokens_config = {}
        
        # Valida permissões de arquivo de tokens se existir
        if self.tokens_path:
            self._validate_file_permissions()
        
        # Emite warning se tokens estiverem em texto plano
        self._warn_plaintext_tokens()
    
    def _load_settings_json(self) -> dict:
        """Carrega configurações do settings.json na raiz do projeto"""
        root_dir = Path(__file__).parent.parent
        settings_file = root_dir / "settings.json"
        
        if not settings_file.exists():
            raise FileNotFoundError(
                f"Arquivo settings.json não encontrado em {root_dir}. "
                "Certifique-se de que o arquivo settings.json existe na raiz do projeto."
            )
        
        try:
            with open(settings_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Erro ao ler settings.json: {e}")
        except IOError as e:
            raise IOError(f"Erro ao abrir settings.json: {e}")
    
    def _load_tokens_config(self) -> dict:
        """Carrega configuração de tokens de arquivo separado"""
        if self.tokens_path and self.tokens_path.exists():
            try:
                import json
                with open(self.tokens_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                warnings.warn(f"Erro ao carregar tokens.json: {e}")
                return {}
        return {}
    
    def _validate_file_permissions(self):
        """Valida permissões de arquivo e emite warning se necessário"""
        if not self.tokens_path or not self.tokens_path.exists():
            return
        
        try:
            import stat
            # Verifica permissões no Windows (stat não funciona da mesma forma)
            if os.name == 'nt':
                # No Windows, verifica se arquivo não está acessível publicamente
                # (verificação básica - Windows tem controle de acesso mais complexo)
                pass
            else:
                # No Linux/Mac, verifica se arquivo tem permissões 600 ou mais restritivas
                file_stat = self.tokens_path.stat()
                mode = file_stat.st_mode
                # Verifica se outros usuários podem ler (octal 004)
                if mode & stat.S_IROTH:
                    warnings.warn(
                        f"AVISO DE SEGURANÇA: O arquivo {self.tokens_path} está acessível "
                        f"por outros usuários. Recomenda-se usar permissões 600 (chmod 600).",
                        UserWarning
                    )
        except Exception:
            # Ignora erros de verificação de permissões
            pass
    
    def _warn_plaintext_tokens(self):
        """Emite warning se tokens estiverem em texto plano"""
        # Verifica se warnings de segurança estão suprimidos
        suppress_warnings = (
            os.getenv("NIBO_SUPPRESS_SECURITY_WARNINGS", "").lower() in ("true", "1", "yes")
            or self._settings_data.get("suppress_security_warnings", False)
        )
        
        if suppress_warnings:
            return
        
        has_plaintext = False
        warnings_messages = []
        
        # Verifica tokens de api_tokens
        api_tokens = self._get_api_tokens_dict()
        if api_tokens:
            for key, token in api_tokens.items():
                if token and not token.startswith("encrypted:"):
                    has_plaintext = True
                    warnings_messages.append(f"Tokens de organizações em api_tokens")
                    break
        
        # Verifica token de obrigações
        obrigacoes_token = self._get_obrigacoes_api_token()
        if obrigacoes_token and not obrigacoes_token.startswith("encrypted:"):
            has_plaintext = True
            warnings_messages.append("Token de obrigações (obrigacoes_api_token)")
        
        if has_plaintext:
            tokens_list = ", ".join(warnings_messages)
            warnings.warn(
                f"AVISO DE SEGURANÇA: Tokens em texto plano detectados no arquivo de configuração ({tokens_list}). "
                "Considere usar criptografia ou variáveis de ambiente para maior segurança.",
                UserWarning
            )
    
    def _get_api_tokens_dict(self) -> Dict[str, str]:
        """Retorna dicionário de tokens do settings.json ou arquivo separado"""
        # Prioriza arquivo separado de tokens
        if self._tokens_config and "api_tokens" in self._tokens_config:
            return self._tokens_config.get("api_tokens", {})
        
        # Carrega do settings.json com prioridade para variáveis de ambiente
        api_tokens = self._settings_data.get("api_tokens", {})
        tokens = {}
        
        for key, value in api_tokens.items():
            # Verifica se há variável de ambiente para este token
            env_var = f"NIBO_API_TOKEN_{key.upper().replace('-', '_')}"
            env_token = os.getenv(env_var)
            if env_token:
                tokens[key] = env_token
            else:
                tokens[key] = value
        
        return tokens
    
    def _decrypt_token(self, encrypted_token: str) -> str:
        """
        Descriptografa um token criptografado
        
        Args:
            encrypted_token: Token com prefixo "encrypted:"
            
        Returns:
            Token descriptografado
            
        Raises:
            ValueError: Se criptografia não estiver disponível ou chave não fornecida
        """
        if not encrypted_token.startswith("encrypted:"):
            return encrypted_token
        
        if not CRYPTOGRAPHY_AVAILABLE:
            raise ValueError(
                "Biblioteca cryptography não está instalada. "
                "Instale com: pip install cryptography"
            )
        
        encryption_key = os.getenv("NIBO_ENCRYPTION_KEY")
        if not encryption_key:
            raise ValueError(
                "Token criptografado encontrado mas NIBO_ENCRYPTION_KEY não está definida. "
                "Configure a variável de ambiente NIBO_ENCRYPTION_KEY com a chave de criptografia."
            )
        
        try:
            # Remove prefixo "encrypted:"
            encrypted_data = encrypted_token[10:]
            
            # Deriva chave da senha usando PBKDF2
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b'nibo_api_salt',  # Salt fixo (em produção, usar salt único por token)
                iterations=100000,
                backend=default_backend()
            )
            key = base64.urlsafe_b64encode(kdf.derive(encryption_key.encode()))
            fernet = Fernet(key)
            
            # Descriptografa
            decrypted = fernet.decrypt(encrypted_data.encode())
            return decrypted.decode()
        except Exception as e:
            raise ValueError(f"Erro ao descriptografar token: {e}")
    
    def _mask_token(self, token: str) -> str:
        """
        Mascara um token para exibição em logs
        
        Args:
            token: Token a mascarar
            
        Returns:
            Token mascarado (mostra apenas últimos 4 caracteres)
        """
        if not token or len(token) <= 4:
            return "****"
        return f"****{token[-4:]}"
    
    def get_api_token(
        self, 
        organizacao_id: Optional[str] = None, 
        organizacao_codigo: Optional[str] = None
    ) -> str:
        """
        Obtém token de API para uma organização específica
        
        Args:
            organizacao_id: ID da organização (ex: "org_123")
            organizacao_codigo: Código simplificado da organização (ex: "empresa_principal")
            
        Returns:
            Token de API
            
        Raises:
            ValueError: Se identificador não for fornecido ou não encontrado
        """
        if not organizacao_id and not organizacao_codigo:
            raise ValueError(
                "É necessário fornecer organizacao_id ou organizacao_codigo. "
                "Use: config.get_api_token(organizacao_id='org_123') ou "
                "config.get_api_token(organizacao_codigo='empresa_principal')"
            )
        
        # Resolve código para ID se necessário
        identificador = organizacao_id
        if organizacao_codigo:
            # Verifica mapeamento de organizações
            organizacoes = self._settings_data.get("organizacoes", {})
            if organizacao_codigo in organizacoes:
                identificador = organizacoes[organizacao_codigo]
            else:
                identificador = organizacao_codigo
        
        if not identificador:
            raise ValueError("Identificador da organização não encontrado")
        
        # Prioridade 1: Variáveis de ambiente
        env_var = f"NIBO_API_TOKEN_{identificador.upper().replace('-', '_')}"
        token = os.getenv(env_var)
        if token:
            # Descriptografa se necessário
            if token.startswith("encrypted:"):
                token = self._decrypt_token(token)
            return token
        
        # Prioridade 2: Settings ou arquivo separado
        api_tokens = self._get_api_tokens_dict()
        token = api_tokens.get(identificador)
        
        if not token:
            # Tenta também com o código original se foi mapeado
            if organizacao_codigo and organizacao_codigo != identificador:
                token = api_tokens.get(organizacao_codigo)
        
        if not token:
            raise ValueError(
                f"Token de API não encontrado para organização '{identificador}'. "
                f"Configure a variável de ambiente {env_var} ou adicione em api_tokens do settings.json"
            )
        
        # Descriptografa se necessário
        if token.startswith("encrypted:"):
            token = self._decrypt_token(token)
        
        return token
    
    def _get_obrigacoes_api_token(self) -> str:
        """Retorna token de API de Obrigações (prioridade: variável de ambiente > settings.json)"""
        return (
            os.getenv("NIBO_OBRIGACOES_API_TOKEN")
            or self._settings_data.get("obrigacoes_api_token", "")
        )
    
    @property
    def obrigacoes_api_token(self) -> str:
        """
        Token de API do Nibo Obrigações
        
        Returns:
            Token de API de Obrigações (prioridade: variável de ambiente > settings.json)
        """
        token = self._get_obrigacoes_api_token()
        if not token:
            raise ValueError(
                "Token de API de Obrigações não encontrado. "
                "Configure NIBO_OBRIGACOES_API_TOKEN como variável de ambiente "
                "ou adicione 'obrigacoes_api_token' em settings.json"
            )
        
        # Descriptografa se necessário
        if token.startswith("encrypted:"):
            token = self._decrypt_token(token)
        
        return token
    
    @property
    def empresa_base_url(self) -> str:
        """
        URL base da API Nibo Empresa
        
        Returns:
            URL base (padrão: https://api.nibo.com.br/empresas/v1)
        """
        return (
            os.getenv("NIBO_EMPRESA_BASE_URL")
            or self._settings_data.get("empresa_base_url")
            or "https://api.nibo.com.br/empresas/v1"
        )
    
    @property
    def obrigacoes_base_url(self) -> str:
        """
        URL base da API Nibo Obrigações
        
        Returns:
            URL base (padrão: https://api.nibo.com.br/accountant/api/v1)
        """
        return (
            os.getenv("NIBO_OBRIGACOES_BASE_URL")
            or self._settings_data.get("obrigacoes_base_url")
            or "https://api.nibo.com.br/accountant/api/v1"
        )
    
    def _get_tokens_path(self) -> Optional[str]:
        """Retorna caminho para arquivo de tokens separado (prioridade: variável de ambiente > settings.json)"""
        return (
            os.getenv("NIBO_TOKENS_FILE")
            or self._settings_data.get("tokens_path")
        )
    
    @property
    def obrigacoes_user_id(self) -> Optional[str]:
        """
        User ID para API Nibo Obrigações (opcional, necessário se token não estiver vinculado a usuário)
        
        Returns:
            User ID (prioridade: variável de ambiente > settings.json)
        """
        return (
            os.getenv("NIBO_OBRIGACOES_USER_ID")
            or self._settings_data.get("obrigacoes_user_id")
        )
