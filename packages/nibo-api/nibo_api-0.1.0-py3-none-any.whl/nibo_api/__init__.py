"""
Nibo API - Cliente Python para integração com a API do Nibo
"""

from nibo_api.settings import NiboSettings
from nibo_api.empresa.client import NiboEmpresaClient
from nibo_api.obrigacoes.client import NiboObrigacoesClient
from nibo_api.common.exceptions import (
    NiboAPIError,
    NiboAuthenticationError,
    NiboNotFoundError,
    NiboValidationError,
    NiboServerError,
    NiboRateLimitError
)

__version__ = "0.1.0"

__all__ = [
    'NiboSettings',
    'NiboEmpresaClient',
    'NiboObrigacoesClient',
    'NiboAPIError',
    'NiboAuthenticationError',
    'NiboNotFoundError',
    'NiboValidationError',
    'NiboServerError',
    'NiboRateLimitError',
]

