"""
Comandos CLI para organizações
"""
import argparse
from typing import Optional, Dict, Any

from nibo_api.settings import NiboSettings
from nibo_api.empresa.client import NiboEmpresaClient
from ..utils import exibir_resultado_json


def listar_organizacoes(
    organizacao_id: Optional[str] = None,
    organizacao_codigo: Optional[str] = None
) -> Dict[str, Any]:
    """
    Lista todas as organizações que o usuário administrador tem acesso
    
    Args:
        organizacao_id: ID da organização para autenticação (ex: "org_123")
        organizacao_codigo: Código simplificado da organização (ex: "empresa_principal")
    
    Returns:
        Dicionário com lista de organizações
    """
    config = NiboSettings()
    # Para listar organizações, precisa de um token inicial
    # Se não fornecido, tenta usar o primeiro token disponível
    if not organizacao_id and not organizacao_codigo:
        api_tokens = config._get_api_tokens_dict()
        if api_tokens:
            # Usa o primeiro token disponível
            primeiro_id = list(api_tokens.keys())[0]
            organizacao_id = primeiro_id
    
    client = NiboEmpresaClient(
        config,
        organizacao_id=organizacao_id,
        organizacao_codigo=organizacao_codigo
    )
    return client.organizacoes.listar_organizacoes()


def handle_organizacoes(args):
    """Handler para comando organizacoes"""
    organizacao_id = None
    organizacao_codigo = None
    if hasattr(args, 'organizacao') and args.organizacao:
        # Tenta determinar se é ID ou código (heurística: IDs geralmente começam com "org_")
        if args.organizacao.startswith("org_") or "-" in args.organizacao:
            organizacao_id = args.organizacao
        else:
            organizacao_codigo = args.organizacao
    
    resultado = listar_organizacoes(
        organizacao_id=organizacao_id,
        organizacao_codigo=organizacao_codigo
    )
    
    if args.json:
        exibir_resultado_json(resultado)
    else:
        # Organizações podem não ter estrutura 'items', então verifica
        if isinstance(resultado, list):
            items = resultado
        else:
            items = resultado.get("items", resultado.get("data", []))
        
        if not items:
            print("Nenhuma organização encontrada.")
        else:
            print(f"Total: {len(items)} organização(ões)")
            print("-" * 80)
            for i, item in enumerate(items, 1):
                if isinstance(item, dict):
                    nome = item.get("name", item.get("organizationName", "N/A"))
                    item_id = item.get("id", item.get("organizationId", "N/A"))
                    print(f"{i}. {nome} (ID: {item_id})")
                else:
                    print(f"{i}. {item}")


def add_organizacoes_parser(subparsers):
    """Adiciona parser para comando organizacoes"""
    parser_organizacoes = subparsers.add_parser(
        "organizacoes",
        help="Lista todas as organizações que o usuário administrador tem acesso"
    )
    parser_organizacoes.add_argument(
        "--json",
        action="store_true",
        help="Exibe resultado em formato JSON"
    )
    parser_organizacoes.add_argument(
        "--org",
        "--organizacao",
        type=str,
        dest="organizacao",
        help="ID ou código da organização (ex: 'org_123' ou 'empresa_principal')"
    )
    parser_organizacoes.set_defaults(func=handle_organizacoes)

