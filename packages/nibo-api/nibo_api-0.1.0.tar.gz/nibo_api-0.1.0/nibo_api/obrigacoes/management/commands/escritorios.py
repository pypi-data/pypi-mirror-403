"""
Comandos CLI para escritórios
"""
import argparse
from typing import Dict, Any

from nibo_api.settings import NiboSettings
from nibo_api.obrigacoes.client import NiboObrigacoesClient
from ..utils import exibir_resultado_json, exibir_lista_simples


def listar_escritorios() -> Dict[str, Any]:
    """
    Lista todos os escritórios contábeis
    
    Returns:
        Dicionário com 'items' (lista de escritórios) e 'metadata'
    """
    config = NiboSettings()
    client = NiboObrigacoesClient(config)
    return client.escritorios.listar()


def handle_escritorios(args):
    """Handler para comando escritorios"""
    resultado = listar_escritorios()
    if args.json:
        exibir_resultado_json(resultado)
    else:
        exibir_lista_simples(resultado, campo_nome="name")
    return 0


def add_escritorios_parser(subparsers):
    """Adiciona parser para comando escritorios"""
    parser_escritorios = subparsers.add_parser(
        "escritorios",
        help="Lista todos os escritórios contábeis"
    )
    parser_escritorios.add_argument(
        "--json",
        action="store_true",
        help="Exibe resultado em formato JSON"
    )
    parser_escritorios.set_defaults(func=handle_escritorios)


