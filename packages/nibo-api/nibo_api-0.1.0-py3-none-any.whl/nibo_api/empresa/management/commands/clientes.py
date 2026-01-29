"""
Comandos CLI para clientes
"""
import argparse
from typing import Optional, Dict, Any

from nibo_api.settings import NiboSettings
from nibo_api.empresa.client import NiboEmpresaClient
from ..utils import exibir_resultado_json, exibir_lista_simples


def listar_clientes(
    nome_cliente: Optional[str] = None,
    organizacao_id: Optional[str] = None,
    organizacao_codigo: Optional[str] = None
) -> Dict[str, Any]:
    """
    Lista clientes
    
    Args:
        nome_cliente: Nome do cliente para filtrar (opcional)
        organizacao_id: ID da organização (ex: "org_123")
        organizacao_codigo: Código simplificado da organização (ex: "empresa_principal")
        
    Returns:
        Dicionário com 'items' (lista de clientes) e 'count'
    """
    config = NiboSettings()
    client = NiboEmpresaClient(
        config,
        organizacao_id=organizacao_id,
        organizacao_codigo=organizacao_codigo
    )
    
    if nome_cliente:
        # Usa contains para busca parcial
        nome_escape = nome_cliente.replace("'", "''")
        return client.clientes.listar(
            odata_filter=f"contains(name, '{nome_escape}')"
        )
    
    return client.clientes.listar()


def criar_cliente(
    nome: str,
    tipo_documento: Optional[str] = None,
    numero_documento: Optional[str] = None,
    organizacao_id: Optional[str] = None,
    organizacao_codigo: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Cria um novo cliente
    
    Args:
        nome: Nome do cliente (obrigatório)
        tipo_documento: Tipo de documento ('cnpj' ou 'cpf', opcional)
        numero_documento: Número do documento (opcional)
        organizacao_id: ID da organização (ex: "org_123")
        organizacao_codigo: Código simplificado da organização (ex: "empresa_principal")
        **kwargs: Outros campos opcionais
        
    Returns:
        Dados do cliente criado
    """
    config = NiboSettings()
    client = NiboEmpresaClient(
        config,
        organizacao_id=organizacao_id,
        organizacao_codigo=organizacao_codigo
    )
    
    return client.clientes.criar(
        name=nome,
        document_type=tipo_documento,
        document_number=numero_documento,
        **kwargs
    )


def handle_clientes(args):
    """Handler para comando clientes"""
    organizacao_id = None
    organizacao_codigo = None
    if hasattr(args, 'organizacao') and args.organizacao:
        if args.organizacao.startswith("org_") or "-" in args.organizacao:
            organizacao_id = args.organizacao
        else:
            organizacao_codigo = args.organizacao
    
    if not organizacao_id and not organizacao_codigo:
        print("ERRO: É necessário fornecer --org (ou --organizacao) para este comando.")
        print("Exemplo: python manage.py empresa clientes --org org_123")
        return 1
    
    resultado = listar_clientes(
        nome_cliente=getattr(args, 'nome', None),
        organizacao_id=organizacao_id,
        organizacao_codigo=organizacao_codigo
    )
    
    if args.json:
        exibir_resultado_json(resultado)
    else:
        exibir_lista_simples(resultado, campo_nome="name")
    
    return 0


def handle_criar_cliente(args):
    """Handler para comando criar-cliente"""
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
    
    try:
        resultado = criar_cliente(
            nome=args.nome,
            tipo_documento=getattr(args, 'tipo_documento', None),
            numero_documento=getattr(args, 'numero_documento', None),
            organizacao_id=organizacao_id,
            organizacao_codigo=organizacao_codigo
        )
        
        if args.json:
            exibir_resultado_json(resultado)
        else:
            print("Cliente criado com sucesso!")
            cliente_id = resultado.get("id", "N/A")
            nome = resultado.get("name", "N/A")
            print(f"ID: {cliente_id}")
            print(f"Nome: {nome}")
    except Exception as e:
        print(f"ERRO ao criar cliente: {e}")
        if args.json:
            import traceback
            traceback.print_exc()
        return 1
    
    return 0


def add_clientes_parser(subparsers):
    """Adiciona parsers para comandos de clientes"""
    # Comando: clientes
    parser_clientes = subparsers.add_parser("clientes", help="Lista clientes")
    parser_clientes.add_argument("--nome", type=str, help="Nome do cliente para filtrar")
    parser_clientes.add_argument(
        "--json",
        action="store_true",
        help="Exibe resultado em formato JSON"
    )
    parser_clientes.add_argument(
        "--org",
        "--organizacao",
        type=str,
        dest="organizacao",
        help="ID ou código da organização (ex: 'org_123' ou 'empresa_principal')"
    )
    parser_clientes.set_defaults(func=handle_clientes)
    
    # Comando: criar-cliente
    parser_criar_cliente = subparsers.add_parser("criar-cliente", aliases=["novo-cliente"], help="Cria um novo cliente")
    parser_criar_cliente.add_argument("--nome", type=str, required=True, help="Nome do cliente")
    parser_criar_cliente.add_argument("--tipo-documento", "-t", type=str, choices=["cnpj", "cpf"], help="Tipo de documento (cnpj ou cpf)")
    parser_criar_cliente.add_argument("--numero-documento", "-ndoc", type=str, help="Número do documento")
    parser_criar_cliente.add_argument(
        "--json",
        action="store_true",
        help="Exibe resultado em formato JSON"
    )
    parser_criar_cliente.add_argument(
        "--org",
        "--organizacao",
        type=str,
        dest="organizacao",
        help="ID ou código da organização (ex: 'org_123' ou 'empresa_principal')"
    )
    parser_criar_cliente.set_defaults(func=handle_criar_cliente)


