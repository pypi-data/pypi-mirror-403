"""
Exceções customizadas para a API Nibo
"""


class NiboAPIError(Exception):
    """Exceção base para erros da API Nibo"""
    pass


class NiboAuthenticationError(NiboAPIError):
    """Erro de autenticação (token inválido ou ausente)"""
    pass


class NiboNotFoundError(NiboAPIError):
    """Recurso não encontrado"""
    pass


class NiboValidationError(NiboAPIError):
    """Erro de validação de dados"""
    pass


class NiboServerError(NiboAPIError):
    """Erro do servidor Nibo"""
    pass


class NiboRateLimitError(NiboAPIError):
    """Limite de requisições excedido"""
    pass

