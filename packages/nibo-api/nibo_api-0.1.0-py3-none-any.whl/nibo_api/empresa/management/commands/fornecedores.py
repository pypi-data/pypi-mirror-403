"""
Comandos CLI para fornecedores
"""
import argparse
from typing import Optional, Dict, Any

from nibo_api.settings import NiboSettings
from nibo_api.empresa.client import NiboEmpresaClient
from ..utils import exibir_resultado_json, exibir_lista_simples


def listar_fornecedores(
    nome_fornecedor: Optional[str] = None,
    organizacao_id: Optional[str] = None,
    organizacao_codigo: Optional[str] = None
) -> Dict[str, Any]:
    """
    Lista fornecedores
    
    Args:
        nome_fornecedor: Nome do fornecedor para filtrar (opcional)
        organizacao_id: ID da organização (ex: "org_123")
        organizacao_codigo: Código simplificado da organização (ex: "empresa_principal")
        
    Returns:
        Dicionário com 'items' (lista de fornecedores) e 'count'
    """
    config = NiboSettings()
    client = NiboEmpresaClient(
        config,
        organizacao_id=organizacao_id,
        organizacao_codigo=organizacao_codigo
    )
    
    if nome_fornecedor:
        nome_escape = nome_fornecedor.replace("'", "''")
        return client.fornecedores.listar(
            odata_filter=f"contains(name, '{nome_escape}')"
        )
    
    return client.fornecedores.listar()


def handle_fornecedores(args):
    """Handler para comando fornecedores"""
    organizacao_id = None
    organizacao_codigo = None
    if hasattr(args, 'organizacao') and args.organizacao:
        if args.organizacao.startswith("org_") or "-" in args.organizacao:
            organizacao_id = args.organizacao
        else:
            organizacao_codigo = args.organizacao
    
    if not organizacao_id and not organizacao_codigo:
        print("ERRO: É necessário fornecer --org (ou --organizacao) para este comando.")
        return 1
    
    resultado = listar_fornecedores(
        nome_fornecedor=getattr(args, 'nome', None),
        organizacao_id=organizacao_id,
        organizacao_codigo=organizacao_codigo
    )
    
    if args.json:
        exibir_resultado_json(resultado)
    else:
        exibir_lista_simples(resultado, campo_nome="name")
    
    return 0


def add_fornecedores_parser(subparsers):
    """Adiciona parser para comando fornecedores"""
    parser_fornecedores = subparsers.add_parser("fornecedores", help="Lista fornecedores")
    parser_fornecedores.add_argument("--nome", type=str, help="Nome do fornecedor para filtrar")
    parser_fornecedores.add_argument(
        "--json",
        action="store_true",
        help="Exibe resultado em formato JSON"
    )
    parser_fornecedores.add_argument(
        "--org",
        "--organizacao",
        type=str,
        dest="organizacao",
        help="ID ou código da organização (ex: 'org_123' ou 'empresa_principal')"
    )
    parser_fornecedores.set_defaults(func=handle_fornecedores)


