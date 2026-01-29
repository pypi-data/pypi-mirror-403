"""
Comandos CLI para categorias
"""
import argparse
from typing import Optional, Dict, Any

from nibo_api.settings import NiboSettings
from nibo_api.empresa.client import NiboEmpresaClient
from ..utils import exibir_resultado_json


def listar_categorias(
    organizacao_id: Optional[str] = None,
    organizacao_codigo: Optional[str] = None
) -> Dict[str, Any]:
    """
    Lista categorias
    
    Args:
        organizacao_id: ID da organização (ex: "org_123")
        organizacao_codigo: Código simplificado da organização (ex: "empresa_principal")
    
    Returns:
        Dicionário com 'items' (lista de categorias) e 'count'
    """
    config = NiboSettings()
    client = NiboEmpresaClient(
        config,
        organizacao_id=organizacao_id,
        organizacao_codigo=organizacao_codigo
    )
    return client.categorias.listar()


def handle_categorias(args):
    """Handler para comando categorias"""
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
    
    resultado = listar_categorias(
        organizacao_id=organizacao_id,
        organizacao_codigo=organizacao_codigo
    )
    
    if args.json:
        exibir_resultado_json(resultado)
    else:
        items = resultado.get("items", [])
        if not items:
            print("Nenhuma categoria encontrada.")
        else:
            print(f"Total: {len(items)} categoria(s)")
            print("-" * 80)
            for i, item in enumerate(items, 1):
                nome = item.get("name", "N/A")
                item_id = item.get("id", "N/A")
                tipo = item.get("type", "N/A")
                print(f"{i}. {nome} (Tipo: {tipo}, ID: {item_id})")
    
    return 0


def add_categorias_parser(subparsers):
    """Adiciona parser para comando categorias"""
    parser_categorias = subparsers.add_parser("categorias", help="Lista categorias")
    parser_categorias.add_argument(
        "--json",
        action="store_true",
        help="Exibe resultado em formato JSON"
    )
    parser_categorias.add_argument(
        "--org",
        "--organizacao",
        type=str,
        dest="organizacao",
        help="ID ou código da organização (ex: 'org_123' ou 'empresa_principal')"
    )
    parser_categorias.set_defaults(func=handle_categorias)


