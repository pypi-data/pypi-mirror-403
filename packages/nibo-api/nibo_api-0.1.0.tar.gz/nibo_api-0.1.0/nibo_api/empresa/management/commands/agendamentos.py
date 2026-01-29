"""
Comandos CLI para agendamentos
"""
import argparse
from typing import Optional, Dict, Any
from uuid import UUID

from nibo_api.settings import NiboSettings
from nibo_api.empresa.client import NiboEmpresaClient
from ..utils import exibir_resultado_json, exibir_agendamentos


def listar_agendamentos_receber(
    tipo: str = "abertos",
    nome_cliente: Optional[str] = None,
    organizacao_id: Optional[str] = None,
    organizacao_codigo: Optional[str] = None
) -> Dict[str, Any]:
    """
    Lista agendamentos de recebimento
    
    Args:
        tipo: Tipo de agendamentos ('abertos', 'vencidos', 'todos')
        nome_cliente: Nome do cliente para filtrar (opcional)
        organizacao_id: ID da organização (ex: "org_123")
        organizacao_codigo: Código simplificado da organização (ex: "empresa_principal")
        
    Returns:
        Dicionário com 'items' (lista de agendamentos) e 'count'
    """
    config = NiboSettings()
    client = NiboEmpresaClient(
        config,
        organizacao_id=organizacao_id,
        organizacao_codigo=organizacao_codigo
    )
    
    odata_filter = None
    if nome_cliente:
        nome_escape = nome_cliente.replace("'", "''")
        odata_filter = f"contains(stakeholder/name, '{nome_escape}')"
    
    if tipo == "abertos":
        return client.agendamentos_receber.listar_abertos(odata_filter=odata_filter)
    elif tipo == "vencidos":
        return client.agendamentos_receber.listar_vencidos(odata_filter=odata_filter)
    else:
        return client.agendamentos_receber.listar_todos(odata_filter=odata_filter)


def listar_agendamentos_pagar(
    tipo: str = "abertos",
    nome_fornecedor: Optional[str] = None,
    organizacao_id: Optional[str] = None,
    organizacao_codigo: Optional[str] = None
) -> Dict[str, Any]:
    """
    Lista agendamentos de pagamento
    
    Args:
        tipo: Tipo de agendamentos ('abertos', 'vencidos', 'todos')
        nome_fornecedor: Nome do fornecedor para filtrar (opcional)
        organizacao_id: ID da organização (ex: "org_123")
        organizacao_codigo: Código simplificado da organização (ex: "empresa_principal")
        
    Returns:
        Dicionário com 'items' (lista de agendamentos) e 'count'
    """
    config = NiboSettings()
    client = NiboEmpresaClient(
        config,
        organizacao_id=organizacao_id,
        organizacao_codigo=organizacao_codigo
    )
    
    odata_filter = None
    if nome_fornecedor:
        nome_escape = nome_fornecedor.replace("'", "''")
        odata_filter = f"contains(stakeholder/name, '{nome_escape}')"
    
    if tipo == "abertos":
        return client.agendamentos_pagar.listar_abertos(odata_filter=odata_filter)
    elif tipo == "vencidos":
        return client.agendamentos_pagar.listar_vencidos(odata_filter=odata_filter)
    else:
        # Para 'todos', usa abertos (a API não tem listar_todos para pagamentos)
        return client.agendamentos_pagar.listar_abertos(odata_filter=odata_filter)


def criar_agendamento_receber(
    cliente_id: str,
    categoria_id: str,
    valor: float,
    data_agendamento: str,
    data_vencimento: str,
    descricao: str,
    referencia: Optional[str] = None,
    organizacao_id: Optional[str] = None,
    organizacao_codigo: Optional[str] = None
) -> Dict[str, Any]:
    """
    Cria um agendamento de recebimento
    
    Args:
        cliente_id: UUID do cliente
        categoria_id: UUID da categoria
        valor: Valor do agendamento
        data_agendamento: Data de agendamento (DD/MM/YYYY)
        data_vencimento: Data de vencimento (DD/MM/YYYY)
        descricao: Descrição do agendamento
        referencia: Referência do agendamento (opcional)
        organizacao_id: ID da organização (ex: "org_123")
        organizacao_codigo: Código simplificado da organização (ex: "empresa_principal")
        
    Returns:
        Dados do agendamento criado
    """
    config = NiboSettings()
    client = NiboEmpresaClient(
        config,
        organizacao_id=organizacao_id,
        organizacao_codigo=organizacao_codigo
    )
    
    categories = [{
        "categoryId": categoria_id,
        "value": valor,
        "description": descricao
    }]
    
    return client.agendamentos_receber.agendar(
        categories=categories,
        stakeholder_id=UUID(cliente_id),
        schedule_date=data_agendamento,
        due_date=data_vencimento,
        description=descricao,
        reference=referencia
    )


def criar_agendamento_pagar(
    fornecedor_id: str,
    categoria_id: str,
    valor: float,
    data_agendamento: str,
    data_vencimento: str,
    descricao: str,
    referencia: Optional[str] = None,
    organizacao_id: Optional[str] = None,
    organizacao_codigo: Optional[str] = None
) -> Dict[str, Any]:
    """
    Cria um agendamento de pagamento
    
    Args:
        fornecedor_id: UUID do fornecedor
        categoria_id: UUID da categoria
        valor: Valor do agendamento
        data_agendamento: Data de agendamento (DD/MM/YYYY)
        data_vencimento: Data de vencimento (DD/MM/YYYY)
        descricao: Descrição do agendamento
        referencia: Referência do agendamento (opcional)
        organizacao_id: ID da organização (ex: "org_123")
        organizacao_codigo: Código simplificado da organização (ex: "empresa_principal")
        
    Returns:
        Dados do agendamento criado
    """
    config = NiboSettings()
    client = NiboEmpresaClient(
        config,
        organizacao_id=organizacao_id,
        organizacao_codigo=organizacao_codigo
    )
    
    categories = [{
        "categoryId": categoria_id,
        "value": valor,
        "description": descricao
    }]
    
    return client.agendamentos_pagar.agendar(
        categories=categories,
        stakeholder_id=UUID(fornecedor_id),
        schedule_date=data_agendamento,
        due_date=data_vencimento,
        description=descricao,
        reference=referencia
    )


def handle_agendamentos_receber(args):
    """Handler para comando agendamentos-receber"""
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
    
    resultado = listar_agendamentos_receber(
        tipo=getattr(args, 'tipo', 'abertos'),
        nome_cliente=getattr(args, 'cliente', None),
        organizacao_id=organizacao_id,
        organizacao_codigo=organizacao_codigo
    )
    
    if args.json:
        exibir_resultado_json(resultado)
    else:
        exibir_agendamentos(resultado, tipo="receber")
    
    return 0


def handle_agendamentos_pagar(args):
    """Handler para comando agendamentos-pagar"""
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
    
    resultado = listar_agendamentos_pagar(
        tipo=getattr(args, 'tipo', 'abertos'),
        nome_fornecedor=getattr(args, 'fornecedor', None),
        organizacao_id=organizacao_id,
        organizacao_codigo=organizacao_codigo
    )
    
    if args.json:
        exibir_resultado_json(resultado)
    else:
        exibir_agendamentos(resultado, tipo="pagar")
    
    return 0


def handle_criar_agendamento_receber(args):
    """Handler para comando criar-agendamento-receber"""
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
        resultado = criar_agendamento_receber(
            cliente_id=args.cliente,
            categoria_id=args.categoria,
            valor=args.valor,
            data_agendamento=args.data_agendamento,
            data_vencimento=args.data_vencimento,
            descricao=args.descricao,
            referencia=getattr(args, 'referencia', None),
            organizacao_id=organizacao_id,
            organizacao_codigo=organizacao_codigo
        )
        
        if args.json:
            exibir_resultado_json(resultado)
        else:
            print("Agendamento de recebimento criado com sucesso!")
            agendamento_id = resultado.get("id", "N/A")
            print(f"ID: {agendamento_id}")
    except Exception as e:
        print(f"ERRO ao criar agendamento: {e}")
        if args.json:
            import traceback
            traceback.print_exc()
        return 1
    
    return 0


def handle_criar_agendamento_pagar(args):
    """Handler para comando criar-agendamento-pagar"""
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
        resultado = criar_agendamento_pagar(
            fornecedor_id=args.fornecedor,
            categoria_id=args.categoria,
            valor=args.valor,
            data_agendamento=args.data_agendamento,
            data_vencimento=args.data_vencimento,
            descricao=args.descricao,
            referencia=getattr(args, 'referencia', None),
            organizacao_id=organizacao_id,
            organizacao_codigo=organizacao_codigo
        )
        
        if args.json:
            exibir_resultado_json(resultado)
        else:
            print("Agendamento de pagamento criado com sucesso!")
            agendamento_id = resultado.get("id", "N/A")
            print(f"ID: {agendamento_id}")
    except Exception as e:
        print(f"ERRO ao criar agendamento: {e}")
        if args.json:
            import traceback
            traceback.print_exc()
        return 1
    
    return 0


def add_agendamentos_parser(subparsers):
    """Adiciona parsers para comandos de agendamentos"""
    # Comando: agendamentos-receber
    parser_agendamentos_receber = subparsers.add_parser(
        "agendamentos-receber",
        aliases=["receber"],
        help="Lista agendamentos de recebimento"
    )
    parser_agendamentos_receber.add_argument(
        "--tipo",
        type=str,
        choices=["abertos", "vencidos", "todos"],
        default="abertos",
        help="Tipo de agendamentos (padrão: abertos)"
    )
    parser_agendamentos_receber.add_argument("--cliente", type=str, help="Nome do cliente para filtrar")
    parser_agendamentos_receber.add_argument(
        "--json",
        action="store_true",
        help="Exibe resultado em formato JSON"
    )
    parser_agendamentos_receber.add_argument(
        "--org",
        "--organizacao",
        type=str,
        dest="organizacao",
        help="ID ou código da organização (ex: 'org_123' ou 'empresa_principal')"
    )
    parser_agendamentos_receber.set_defaults(func=handle_agendamentos_receber)
    
    # Comando: agendamentos-pagar
    parser_agendamentos_pagar = subparsers.add_parser(
        "agendamentos-pagar",
        aliases=["pagar"],
        help="Lista agendamentos de pagamento"
    )
    parser_agendamentos_pagar.add_argument(
        "--tipo",
        type=str,
        choices=["abertos", "vencidos", "todos"],
        default="abertos",
        help="Tipo de agendamentos (padrão: abertos)"
    )
    parser_agendamentos_pagar.add_argument("--fornecedor", type=str, help="Nome do fornecedor para filtrar")
    parser_agendamentos_pagar.add_argument(
        "--json",
        action="store_true",
        help="Exibe resultado em formato JSON"
    )
    parser_agendamentos_pagar.add_argument(
        "--org",
        "--organizacao",
        type=str,
        dest="organizacao",
        help="ID ou código da organização (ex: 'org_123' ou 'empresa_principal')"
    )
    parser_agendamentos_pagar.set_defaults(func=handle_agendamentos_pagar)
    
    # Comando: criar-agendamento-receber
    parser_criar_agendamento_receber = subparsers.add_parser(
        "criar-agendamento-receber",
        aliases=["novo-receber"],
        help="Cria um agendamento de recebimento"
    )
    parser_criar_agendamento_receber.add_argument("--cliente", "-cli", type=str, required=True, help="UUID do cliente")
    parser_criar_agendamento_receber.add_argument("--categoria", "-cat", type=str, required=True, help="UUID da categoria")
    parser_criar_agendamento_receber.add_argument("--valor", type=float, required=True, help="Valor do agendamento")
    parser_criar_agendamento_receber.add_argument("--data-agendamento", "-da", type=str, required=True, help="Data de agendamento (DD/MM/YYYY)")
    parser_criar_agendamento_receber.add_argument("--data-vencimento", "-dv", type=str, required=True, help="Data de vencimento (DD/MM/YYYY)")
    parser_criar_agendamento_receber.add_argument("--descricao", type=str, required=True, help="Descrição do agendamento")
    parser_criar_agendamento_receber.add_argument("--referencia", type=str, help="Referência do agendamento (opcional)")
    parser_criar_agendamento_receber.add_argument(
        "--json",
        action="store_true",
        help="Exibe resultado em formato JSON"
    )
    parser_criar_agendamento_receber.add_argument(
        "--org",
        "--organizacao",
        type=str,
        dest="organizacao",
        help="ID ou código da organização (ex: 'org_123' ou 'empresa_principal')"
    )
    parser_criar_agendamento_receber.set_defaults(func=handle_criar_agendamento_receber)
    
    # Comando: criar-agendamento-pagar
    parser_criar_agendamento_pagar = subparsers.add_parser(
        "criar-agendamento-pagar",
        help="Cria um agendamento de pagamento"
    )
    parser_criar_agendamento_pagar.add_argument("--fornecedor", "-for", type=str, required=True, help="UUID do fornecedor")
    parser_criar_agendamento_pagar.add_argument("--categoria", "-cat", type=str, required=True, help="UUID da categoria")
    parser_criar_agendamento_pagar.add_argument("--valor", type=float, required=True, help="Valor do agendamento")
    parser_criar_agendamento_pagar.add_argument("--data-agendamento", "-da", type=str, required=True, help="Data de agendamento (DD/MM/YYYY)")
    parser_criar_agendamento_pagar.add_argument("--data-vencimento", "-dv", type=str, required=True, help="Data de vencimento (DD/MM/YYYY)")
    parser_criar_agendamento_pagar.add_argument("--descricao", type=str, required=True, help="Descrição do agendamento")
    parser_criar_agendamento_pagar.add_argument("--referencia", type=str, help="Referência do agendamento (opcional)")
    parser_criar_agendamento_pagar.add_argument(
        "--json",
        action="store_true",
        help="Exibe resultado em formato JSON"
    )
    parser_criar_agendamento_pagar.add_argument(
        "--org",
        "--organizacao",
        type=str,
        dest="organizacao",
        help="ID ou código da organização (ex: 'org_123' ou 'empresa_principal')"
    )
    parser_criar_agendamento_pagar.set_defaults(func=handle_criar_agendamento_pagar)


