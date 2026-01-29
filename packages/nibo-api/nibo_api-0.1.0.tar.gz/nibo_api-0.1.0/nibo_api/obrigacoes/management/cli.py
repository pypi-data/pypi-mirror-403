"""
Comandos CLI principais para Nibo Obrigações
Importa e adapta funções de obrigacoes.py para usar NiboSettings
"""
import argparse
import mimetypes
import re
from datetime import date
from pathlib import Path
from typing import Optional, List, Dict, Any
from uuid import UUID

from nibo_api.settings import NiboSettings
from nibo_api.obrigacoes.client import NiboObrigacoesClient
from nibo_api.obrigacoes.tarefas import (
    interpretar_status,
    interpretar_skip_holiday,
    interpretar_frequency,
    interpretar_frequency_schedule
)
from .utils import (
    parse_date,
    format_date,
    exibir_resultado_json,
    exibir_lista_simples,
    exibir_obrigacoes
)


# Importa todas as funções de negócio de obrigacoes.py e adapta para usar NiboSettings
# (substituindo NiboConfig por NiboSettings)

def listar_escritorios() -> Dict[str, Any]:
    """Lista todos os escritórios contábeis"""
    config = NiboSettings()
    client = NiboObrigacoesClient(config)
    return client.escritorios.listar()


def listar_clientes(accounting_firm_id: Optional[UUID] = None, nome_cliente: Optional[str] = None) -> Dict[str, Any]:
    """Lista clientes de um escritório contábil"""
    config = NiboSettings()
    client = NiboObrigacoesClient(config)
    
    if accounting_firm_id is None:
        escritorios = client.escritorios.listar()
        if not escritorios.get("items"):
            raise ValueError("Nenhum escritório encontrado")
        accounting_firm_id = UUID(escritorios["items"][0]["id"])
    
    if nome_cliente:
        nome_escape = nome_cliente.replace("'", "''")
        return client.clientes.listar(
            accounting_firm_id=accounting_firm_id,
            odata_filter=f"contains(name, '{nome_escape}')"
        )
    
    return client.clientes.listar(accounting_firm_id=accounting_firm_id)


def listar_contatos(accounting_firm_id: Optional[UUID] = None) -> Dict[str, Any]:
    """Lista contatos de um escritório contábil"""
    config = NiboSettings()
    client = NiboObrigacoesClient(config)
    
    if accounting_firm_id is None:
        escritorios = client.escritorios.listar()
        if not escritorios.get("items"):
            raise ValueError("Nenhum escritório encontrado")
        accounting_firm_id = UUID(escritorios["items"][0]["id"])
    
    return client.contatos.listar(accounting_firm_id=accounting_firm_id)


def listar_obrigacoes_cliente(
    cliente_identificador: str,
    data_inicio: Optional[date] = None,
    data_fim: Optional[date] = None,
    accounting_firm_id: Optional[UUID] = None
) -> Dict[str, Any]:
    """Lista obrigações de um cliente específico"""
    config = NiboSettings()
    client = NiboObrigacoesClient(config)
    
    if accounting_firm_id is None:
        escritorios = client.escritorios.listar()
        if not escritorios.get("items"):
            raise ValueError("Nenhum escritório encontrado")
        accounting_firm_id = UUID(escritorios["items"][0]["id"])
    
    clientes_encontrados = []
    
    try:
        cliente_id = UUID(cliente_identificador)
        cliente_encontrado = None
        skip = 0
        page_size = 100
        
        while cliente_encontrado is None:
            clientes = client.clientes.listar(
                accounting_firm_id=accounting_firm_id,
                odata_top=page_size,
                odata_skip=skip
            )
            
            items = clientes.get("items", [])
            if not items:
                break
            
            for cliente in items:
                if str(cliente.get("id")) == str(cliente_id):
                    cliente_encontrado = cliente
                    break
            
            if cliente_encontrado:
                break
            
            skip += len(items)
            if skip >= 1000:
                break
        
        if cliente_encontrado is None:
            raise ValueError(f"Cliente com ID '{cliente_identificador}' não encontrado")
        
        clientes_encontrados = [cliente_encontrado]
    except ValueError:
        nome_cliente = cliente_identificador
        nome_escape = nome_cliente.replace("'", "''")
        clientes = client.clientes.listar(
            accounting_firm_id=accounting_firm_id,
            odata_filter=f"contains(name, '{nome_escape}')"
        )
        
        if not clientes.get("items") or len(clientes["items"]) == 0:
            raise ValueError(f"Cliente '{nome_cliente}' não encontrado")
        
        clientes_encontrados = clientes["items"]
    
    if not clientes_encontrados:
        raise ValueError(f"Erro ao identificar o cliente: '{cliente_identificador}'")
    
    if data_inicio is None:
        data_inicio = date.today()
    if data_fim is None:
        ano_atual = date.today().year
        data_fim = date(ano_atual, 12, 31)
    
    cliente_ids = [UUID(cliente.get("id")) for cliente in clientes_encontrados]
    ids_str = "', '".join(str(cid) for cid in cliente_ids)
    filtro_cliente = f"Customer/Id in ('{ids_str}')"
    
    items = []
    try:
        relatorios = client.relatorios.listar_relatorios(
            accounting_firm_id=accounting_firm_id,
            odata_filter=filtro_cliente,
            odata_orderby="filedDate desc"
        )
        items = relatorios.get("items", [])
    except Exception:
        try:
            relatorios = client.relatorios.listar_relatorios(
                accounting_firm_id=accounting_firm_id,
                odata_filter=filtro_cliente
            )
            items = relatorios.get("items", [])
        except Exception:
            relatorios = client.relatorios.listar_relatorios(
                accounting_firm_id=accounting_firm_id
            )
            items = relatorios.get("items", [])
            
            items_cliente = []
            cliente_ids_str = [str(cid) for cid in cliente_ids]
            for item in items:
                customer = item.get("customer")
                if customer and isinstance(customer, dict):
                    customer_id_item = customer.get("id")
                    if customer_id_item and str(customer_id_item) in cliente_ids_str:
                        items_cliente.append(item)
            items = items_cliente
    
    items_filtrados = []
    for item in items:
        duedate_str = item.get("dueDate")
        duedate_obj = parse_date(duedate_str)
        
        if duedate_obj and data_inicio <= duedate_obj <= data_fim:
            items_filtrados.append(item)
    
    return {
        "items": items_filtrados,
        "total_cliente": len(items),
        "total_periodo": len(items_filtrados),
        "clientes_info": clientes_encontrados,
        "total_clientes": len(clientes_encontrados),
        "periodo": {
            "inicio": data_inicio,
            "fim": data_fim
        }
    }


def listar_departamentos(accounting_firm_id: Optional[UUID] = None) -> Dict[str, Any]:
    """Lista departamentos de um escritório contábil"""
    config = NiboSettings()
    client = NiboObrigacoesClient(config)
    
    if accounting_firm_id is None:
        escritorios = client.escritorios.listar()
        if not escritorios.get("items"):
            raise ValueError("Nenhum escritório encontrado")
        accounting_firm_id = UUID(escritorios["items"][0]["id"])
    
    return client.departamentos.listar(accounting_firm_id=accounting_firm_id)


def listar_tarefas(
    accounting_firm_id: Optional[UUID] = None,
    usuario_id: Optional[UUID] = None,
    usuario_nome: Optional[str] = None,
    incluir_completas: bool = False
) -> Dict[str, Any]:
    """Lista tarefas de um escritório contábil"""
    config = NiboSettings()
    client = NiboObrigacoesClient(config)
    
    if accounting_firm_id is None:
        escritorios = client.escritorios.listar()
        if not escritorios.get("items"):
            raise ValueError("Nenhum escritório encontrado")
        accounting_firm_id = UUID(escritorios["items"][0]["id"])
    
    filtros = []
    
    if not incluir_completas:
        filtros.append("status ne 3")
    
    if usuario_id:
        filtros.append(f"inChargeUser/Id eq '{usuario_id}'")
    elif usuario_nome:
        nome_escape = usuario_nome.replace("'", "''")
        filtros.append(f"contains(inChargeUser/Name, '{nome_escape}')")
    
    odata_filter = " and ".join(filtros) if filtros else None
    
    return client.tarefas.listar(
        accounting_firm_id=accounting_firm_id,
        odata_filter=odata_filter
    )


def criar_tarefa(
    nome: str,
    accounting_firm_id: Optional[UUID] = None,
    template_id: Optional[str] = None,
    deadline: Optional[str] = None,
    usuario_responsavel_id: Optional[str] = None,
    cliente_id: Optional[str] = None,
    descricao: Optional[str] = None,
    departamento_id: Optional[str] = None,
    arquivo_ids: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Cria uma nova tarefa"""
    config = NiboSettings()
    client = NiboObrigacoesClient(config)
    
    if accounting_firm_id is None:
        escritorios = client.escritorios.listar()
        if not escritorios.get("items"):
            raise ValueError("Nenhum escritório encontrado")
        accounting_firm_id = UUID(escritorios["items"][0]["id"])
    
    return client.tarefas.criar(
        accounting_firm_id=accounting_firm_id,
        name=nome,
        task_template_id=template_id,
        deadline=deadline,
        in_charge_user_id=usuario_responsavel_id,
        customer_id=cliente_id,
        description=descricao,
        department_id=departamento_id,
        file_ids=arquivo_ids
    )


def listar_cnaes(accounting_firm_id: Optional[UUID] = None) -> Dict[str, Any]:
    """Lista CNAEs de um escritório contábil"""
    config = NiboSettings()
    client = NiboObrigacoesClient(config)
    
    if accounting_firm_id is None:
        escritorios = client.escritorios.listar()
        if not escritorios.get("items"):
            raise ValueError("Nenhum escritório encontrado")
        accounting_firm_id = UUID(escritorios["items"][0]["id"])
    
    return client.cnaes.listar(accounting_firm_id=accounting_firm_id)


def listar_grupos_clientes(accounting_firm_id: Optional[UUID] = None) -> Dict[str, Any]:
    """Lista grupos de clientes (tags) de um escritório contábil"""
    config = NiboSettings()
    client = NiboObrigacoesClient(config)
    
    if accounting_firm_id is None:
        escritorios = client.escritorios.listar()
        if not escritorios.get("items"):
            raise ValueError("Nenhum escritório encontrado")
        accounting_firm_id = UUID(escritorios["items"][0]["id"])
    
    return client.grupos_clientes.listar(accounting_firm_id=accounting_firm_id)


def listar_usuarios(accounting_firm_id: Optional[UUID] = None, nome_usuario: Optional[str] = None) -> Dict[str, Any]:
    """Lista membros da equipe de um escritório contábil"""
    config = NiboSettings()
    client = NiboObrigacoesClient(config)
    
    if accounting_firm_id is None:
        escritorios = client.escritorios.listar()
        if not escritorios.get("items"):
            raise ValueError("Nenhum escritório encontrado")
        accounting_firm_id = UUID(escritorios["items"][0]["id"])
    
    odata_filter = None
    if nome_usuario:
        nome_escape = nome_usuario.replace("'", "''")
        odata_filter = f"contains(name, '{nome_escape}')"
    
    return client.usuarios.listar_membros_equipe(
        accounting_firm_id=accounting_firm_id,
        odata_filter=odata_filter
    )


def criar_arquivo(
    caminho_arquivo: str,
    accounting_firm_id: Optional[UUID] = None,
    nome_arquivo: Optional[str] = None
) -> Dict[str, Any]:
    """Cria um arquivo na API para upload"""
    config = NiboSettings()
    client = NiboObrigacoesClient(config)
    
    arquivo_path = Path(caminho_arquivo)
    if not arquivo_path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho_arquivo}")
    
    if nome_arquivo is None:
        nome_arquivo = arquivo_path.name
    
    if accounting_firm_id is None:
        escritorios = client.escritorios.listar()
        if not escritorios.get("items"):
            raise ValueError("Nenhum escritório encontrado")
        accounting_firm_id = UUID(escritorios["items"][0]["id"])
    
    resultado = client.arquivos.criar_arquivo_upload(
        accounting_firm_id=accounting_firm_id,
        name=nome_arquivo
    )
    
    return resultado


def fazer_upload_arquivo(
    caminho_arquivo: str,
    shared_access_signature: Optional[str] = None,
    file_id: Optional[str] = None,
    accounting_firm_id: Optional[UUID] = None
) -> Dict[str, Any]:
    """Faz upload de um arquivo usando sharedAccessSignature e envia para conferência"""
    config = NiboSettings()
    client = NiboObrigacoesClient(config)
    
    arquivo_path = Path(caminho_arquivo)
    if not arquivo_path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho_arquivo}")
    
    if not shared_access_signature and not file_id:
        raise ValueError("É necessário fornecer --shared-access-signature ou --file")
    
    if shared_access_signature and not file_id:
        match = re.search(r'/files/([a-f0-9\-]{36})', shared_access_signature)
        if match:
            file_id = match.group(1)
        else:
            raise ValueError("Não foi possível extrair o ID do arquivo da URL sharedAccessSignature")
    
    if file_id and not shared_access_signature:
        raise ValueError(
            "Para usar --file, é necessário ter a sharedAccessSignature salva. "
            "Recomenda-se usar --shared-access-signature diretamente."
        )
    
    if accounting_firm_id is None:
        escritorios = client.escritorios.listar()
        if not escritorios.get("items"):
            raise ValueError("Nenhum escritório encontrado")
        accounting_firm_id = UUID(escritorios["items"][0]["id"])
    
    content_type, _ = mimetypes.guess_type(str(arquivo_path))
    if not content_type:
        content_type = "application/octet-stream"
    
    with open(arquivo_path, "rb") as f:
        file_content = f.read()
    
    response = client.arquivos.fazer_upload(
        shared_access_signature=shared_access_signature,
        file_content=file_content,
        content_type=content_type
    )
    
    upload_success = response.status_code in [200, 201, 204]
    
    resultado = {
        "status_code": response.status_code,
        "status": "success" if upload_success else "error",
        "file_path": str(arquivo_path),
        "file_size": len(file_content),
        "content_type": content_type,
        "file_id": file_id
    }
    
    if upload_success:
        try:
            conferencia_resultado = client.conferencia.enviar_arquivo_conferencia(
                accounting_firm_id=accounting_firm_id,
                file_id=UUID(file_id)
            )
            resultado["conferencia"] = {
                "status": "success",
                "resultado": conferencia_resultado
            }
        except Exception as e:
            resultado["conferencia"] = {
                "status": "error",
                "erro": str(e)
            }
    
    return resultado


def main_cli():
    """Interface de linha de comando principal"""
    parser = argparse.ArgumentParser(
        description="CLI para interagir com a API Nibo Obrigações",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:

  # Listar escritórios
  python manage.py obrigacoes escritorios

  # Listar clientes
  python manage.py obrigacoes clientes
  python manage.py obrigacoes clientes --nome "BV - BRAGGION & VILACA LTDA"

  # Listar obrigações de um cliente
  python manage.py obrigacoes obrigacoes --cliente "BV - BRAGGION & VILACA LTDA"
  python manage.py obrigacoes obrigacoes --cliente "BV" --inicio 01/01/2025 --fim 31/12/2025

  # Listar contatos
  python manage.py obrigacoes contatos

  # Listar departamentos
  python manage.py obrigacoes departamentos

  # Listar tarefas
  python manage.py obrigacoes tarefas
  python manage.py obrigacoes tarefas --usuario-nome "João"
  python manage.py obrigacoes tarefas --usuario "uuid-do-usuario"

  # Listar CNAEs
  python manage.py obrigacoes cnaes

  # Listar grupos de clientes
  python manage.py obrigacoes grupos-clientes

  # Listar usuários
  python manage.py obrigacoes usuarios

  # Criar arquivo
  python manage.py obrigacoes criar-arquivo --arquivo "etc/arquivo.pdf"

  # Fazer upload de arquivo
  python manage.py obrigacoes upload-arquivo --arquivo "etc/arquivo.pdf" --shared-access-signature "https://..."

  # Usar formato JSON
  python manage.py obrigacoes clientes --json
        """
    )
    
    subparsers = parser.add_subparsers(dest="comando", help="Comandos disponíveis")
    
    shared_args = argparse.ArgumentParser(add_help=False)
    shared_args.add_argument(
        "--escritorio",
        "-e",
        type=str,
        help="UUID do escritório contábil (opcional, usa o primeiro disponível se não fornecido)"
    )
    shared_args.add_argument(
        "--json",
        action="store_true",
        help="Exibe resultado em formato JSON"
    )
    
    parser_escritorios = subparsers.add_parser("escritorios", help="Lista todos os escritórios contábeis", parents=[shared_args])
    parser_clientes = subparsers.add_parser("clientes", help="Lista clientes de um escritório", parents=[shared_args])
    parser_clientes.add_argument("--nome", type=str, help="Nome do cliente para filtrar")
    parser_obrigacoes = subparsers.add_parser("obrigacoes", help="Lista obrigações de um cliente", parents=[shared_args])
    parser_obrigacoes.add_argument("--cliente", type=str, required=True, help="Nome do cliente ou UUID do cliente")
    parser_obrigacoes.add_argument("--inicio", type=str, help="Data de início (DD/MM/YYYY, padrão: hoje)")
    parser_obrigacoes.add_argument("--fim", type=str, help="Data de fim (DD/MM/YYYY, padrão: 31/12 do ano atual)")
    parser_obrigacoes.add_argument("--simples", action="store_true", help="Exibe apenas informações básicas")
    parser_contatos = subparsers.add_parser("contatos", help="Lista contatos de um escritório", parents=[shared_args])
    parser_departamentos = subparsers.add_parser("departamentos", help="Lista departamentos de um escritório", parents=[shared_args])
    parser_tarefas = subparsers.add_parser("tarefas", help="Lista tarefas de um escritório", parents=[shared_args])
    parser_tarefas.add_argument("--usuario", "-u", type=str, help="UUID do usuário para filtrar tarefas")
    parser_tarefas.add_argument("--usuario-nome", "-un", type=str, help="Nome do usuário para filtrar tarefas (busca parcial)")
    parser_tarefas.add_argument("--incluir-completas", "-ic", action="store_true", help="Inclui tarefas completas (padrão: exclui tarefas completas)")
    parser_criar_tarefa = subparsers.add_parser("criar-tarefa", aliases=["nova-tarefa"], help="Cria uma nova tarefa", parents=[shared_args])
    parser_criar_tarefa.add_argument("--nome", type=str, required=True, help="Nome da tarefa (obrigatório se não usar template)")
    parser_criar_tarefa.add_argument("--template", type=str, help="ID do template para criar tarefa a partir de template")
    parser_criar_tarefa.add_argument("--deadline", type=str, help="Data e hora limite (formato: YYYY-MM-DDTHH:MM:SS ou YYYY-MM-DD)")
    parser_criar_tarefa.add_argument("--usuario-responsavel-id", "-r", type=str, help="ID do usuário responsável")
    parser_criar_tarefa.add_argument("--cliente", "-cli", type=str, help="ID do cliente associado")
    parser_criar_tarefa.add_argument("--descricao", type=str, help="Descrição da tarefa")
    parser_criar_tarefa.add_argument("--departamento", "-dep", type=str, help="ID do departamento relacionado")
    parser_criar_tarefa.add_argument("--arquivos", "-a", type=str, nargs="+", help="IDs de arquivos anexados (separados por espaço)")
    parser_cnaes = subparsers.add_parser("cnaes", help="Lista CNAEs de um escritório", parents=[shared_args])
    parser_grupos = subparsers.add_parser("grupos-clientes", help="Lista grupos de clientes (tags)", parents=[shared_args])
    parser_usuarios = subparsers.add_parser("usuarios", help="Lista membros da equipe", parents=[shared_args])
    parser_usuarios.add_argument("--nome", type=str, help="Nome do usuário para filtrar (busca parcial)")
    parser_criar_arquivo = subparsers.add_parser("criar-arquivo", aliases=["novo-arquivo"], help="Cria um arquivo na API para upload", parents=[shared_args])
    parser_criar_arquivo.add_argument("--arquivo", type=str, required=True, help="Caminho do arquivo local (obrigatório)")
    parser_criar_arquivo.add_argument("--nome", type=str, help="Nome do arquivo (opcional, usa nome do arquivo local se não fornecido)")
    parser_upload_arquivo = subparsers.add_parser("upload-arquivo", aliases=["upload"], help="Faz upload de um arquivo usando sharedAccessSignature", parents=[shared_args])
    parser_upload_arquivo.add_argument("--arquivo", type=str, required=True, help="Caminho do arquivo local (obrigatório)")
    parser_upload_arquivo.add_argument("--shared-access-signature", "-sas", type=str, help="URL temporária para upload (obrigatório se não usar --file)")
    parser_upload_arquivo.add_argument("--file", "-f", type=str, help="ID do arquivo criado (obrigatório se não usar shared-access-signature)")
    
    # Se chamado via manage.py, remove o primeiro argumento ("obrigacoes")
    import sys
    if len(sys.argv) > 0 and sys.argv[0].endswith("manage.py") and len(sys.argv) > 1 and sys.argv[1] == "obrigacoes":
        # Remove "obrigacoes" dos argumentos
        sys.argv = [sys.argv[0]] + sys.argv[2:]
    
    args = parser.parse_args()
    
    if not args.comando:
        parser.print_help()
        return 0
    
    accounting_firm_id = None
    if hasattr(args, 'escritorio') and args.escritorio:
        try:
            accounting_firm_id = UUID(args.escritorio)
        except ValueError:
            print(f"ERRO: ID do escritório inválido: {args.escritorio}")
            return 1
    
    try:
        if args.comando == "escritorios":
            resultado = listar_escritorios()
            if args.json:
                exibir_resultado_json(resultado)
            else:
                exibir_lista_simples(resultado, campo_nome="name")
        
        elif args.comando == "clientes":
            resultado = listar_clientes(
                accounting_firm_id=accounting_firm_id,
                nome_cliente=args.nome
            )
            if args.json:
                exibir_resultado_json(resultado)
            else:
                exibir_lista_simples(resultado, campo_nome="name")
        
        elif args.comando == "obrigacoes":
            data_inicio = None
            data_fim = None
            
            if args.inicio:
                data_inicio = parse_date(args.inicio)
                if not data_inicio:
                    print(f"ERRO: Data de início inválida: {args.inicio}. Use formato DD/MM/YYYY")
                    return 1
            
            if args.fim:
                data_fim = parse_date(args.fim)
                if not data_fim:
                    print(f"ERRO: Data de fim inválida: {args.fim}. Use formato DD/MM/YYYY")
                    return 1
            
            obrigacoes = listar_obrigacoes_cliente(
                cliente_identificador=args.cliente,
                data_inicio=data_inicio,
                data_fim=data_fim,
                accounting_firm_id=accounting_firm_id
            )
            
            if args.json:
                exibir_resultado_json(obrigacoes)
            else:
                exibir_obrigacoes(obrigacoes, detalhado=not args.simples)
        
        elif args.comando == "contatos":
            resultado = listar_contatos(accounting_firm_id=accounting_firm_id)
            if args.json:
                exibir_resultado_json(resultado)
            else:
                exibir_lista_simples(resultado, campo_nome="name")
        
        elif args.comando == "departamentos":
            resultado = listar_departamentos(accounting_firm_id=accounting_firm_id)
            if args.json:
                exibir_resultado_json(resultado)
            else:
                exibir_lista_simples(resultado, campo_nome="name")
        
        elif args.comando == "tarefas":
            usuario_id = None
            if hasattr(args, 'usuario') and args.usuario:
                try:
                    usuario_id = UUID(args.usuario)
                except ValueError:
                    print(f"ERRO: ID do usuário inválido: {args.usuario}")
                    return 1
            
            resultado = listar_tarefas(
                accounting_firm_id=accounting_firm_id,
                usuario_id=usuario_id,
                usuario_nome=args.usuario_nome,
                incluir_completas=args.incluir_completas
            )
            if args.json:
                exibir_resultado_json(resultado)
            else:
                items = resultado.get("items", [])
                if not items:
                    print("Nenhuma tarefa encontrada.")
                else:
                    filtro_info = ""
                    if (hasattr(args, 'usuario') and args.usuario) or args.usuario_nome:
                        if hasattr(args, 'usuario') and args.usuario:
                            filtro_info = f" (filtrado por usuário ID: {args.usuario})"
                        elif args.usuario_nome:
                            filtro_info = f" (filtrado por usuário: {args.usuario_nome})"
                    
                    print(f"Total: {len(items)} tarefa(s){filtro_info}")
                    print("-" * 100)
                    print(f"{'Nome':<40} {'Status':<15} {'Frequência':<20} {'Usuário':<25} {'ID':<40}")
                    print("-" * 100)
                    for i, item in enumerate(items, 1):
                        nome = item.get("name", "N/A")
                        status_val = item.get("status", 0)
                        status = interpretar_status(status_val)
                        frequency_val = item.get("frequency", 0)
                        frequency = interpretar_frequency(frequency_val)
                        item_id = item.get("id", "N/A")
                        
                        in_charge_user = item.get("inChargeUser", {})
                        usuario_nome = in_charge_user.get("name", "N/A") if isinstance(in_charge_user, dict) else "N/A"
                        
                        nome_display = nome[:37] + "..." if len(nome) > 40 else nome
                        usuario_display = usuario_nome[:22] + "..." if len(usuario_nome) > 25 else usuario_nome
                        print(f"{nome_display:<40} {status:<15} {frequency:<20} {usuario_display:<25} {item_id:<40}")
                        
                        if frequency_val > 0:
                            schedule = item.get("frequencySchedule", 0)
                            if schedule > 0:
                                dias = interpretar_frequency_schedule(schedule)
                                print(f"   Dias: {', '.join(dias)}")
                        
                        skip_holiday = item.get("skipHoliday", 0)
                        if skip_holiday > 0:
                            regra = interpretar_skip_holiday(skip_holiday)
                            print(f"   Regra feriados: {regra}")
                    
                    print("-" * 100)
        
        elif args.comando == "criar-tarefa":
            try:
                resultado = criar_tarefa(
                    nome=args.nome,
                    accounting_firm_id=accounting_firm_id,
                    template_id=getattr(args, 'template', None),
                    deadline=args.deadline,
                    usuario_responsavel_id=args.usuario_responsavel_id,
                    cliente_id=getattr(args, 'cliente', None),
                    descricao=args.descricao,
                    departamento_id=getattr(args, 'departamento', None),
                    arquivo_ids=getattr(args, 'arquivos', None)
                )
                
                if args.json:
                    exibir_resultado_json(resultado)
                else:
                    print("Tarefa criada com sucesso!")
                    print("Status: 202 Accepted (criação assíncrona)")
                    if resultado:
                        print(f"Resposta: {resultado}")
            except Exception as e:
                print(f"ERRO ao criar tarefa: {e}")
                if args.json:
                    import traceback
                    traceback.print_exc()
                return 1
        
        elif args.comando == "cnaes":
            resultado = listar_cnaes(accounting_firm_id=accounting_firm_id)
            if args.json:
                exibir_resultado_json(resultado)
            else:
                items = resultado.get("items", [])
                if not items:
                    print("Nenhum CNAE encontrado.")
                else:
                    print(f"Total: {len(items)} CNAE(s)")
                    print("-" * 80)
                    for i, item in enumerate(items, 1):
                        codigo = item.get("code", "N/A")
                        descricao = item.get("description", "N/A")
                        print(f"{i}. {codigo} - {descricao[:50]}...")
        
        elif args.comando == "grupos-clientes":
            resultado = listar_grupos_clientes(accounting_firm_id=accounting_firm_id)
            if args.json:
                exibir_resultado_json(resultado)
            else:
                exibir_lista_simples(resultado, campo_nome="name")
        
        elif args.comando == "usuarios":
            resultado = listar_usuarios(accounting_firm_id=accounting_firm_id, nome_usuario=args.nome)
            if args.json:
                exibir_resultado_json(resultado)
            else:
                items = resultado.get("items", [])
                if not items:
                    print("Nenhum usuário encontrado.")
                else:
                    print(f"Total: {len(items)} usuário(s)")
                    print("-" * 80)
                    for i, item in enumerate(items, 1):
                        nome = item.get("name", "N/A")
                        email = item.get("email", "N/A")
                        item_id = item.get("id", "N/A")
                        print(f"{i}. {nome} ({email}) - ID: {item_id}")
        
        elif args.comando == "criar-arquivo":
            try:
                resultado = criar_arquivo(
                    caminho_arquivo=args.arquivo,
                    accounting_firm_id=accounting_firm_id,
                    nome_arquivo=getattr(args, 'nome', None)
                )
                
                if args.json:
                    exibir_resultado_json(resultado)
                else:
                    file_id = resultado.get("id", "N/A")
                    shared_access = resultado.get("sharedAccessSignature", "N/A")
                    print("Arquivo criado com sucesso!")
                    print(f"ID do arquivo: {file_id}")
                    print(f"sharedAccessSignature: {shared_access}")
                    print("\nIMPORTANTE: A URL sharedAccessSignature é válida por apenas 10 minutos.")
                    print("Use o comando 'upload-arquivo' para fazer o upload do arquivo.")
            except Exception as e:
                print(f"ERRO ao criar arquivo: {e}")
                if args.json:
                    import traceback
                    traceback.print_exc()
                return 1
        
        elif args.comando == "upload-arquivo":
            try:
                resultado = fazer_upload_arquivo(
                    caminho_arquivo=args.arquivo,
                    shared_access_signature=getattr(args, 'shared_access_signature', None),
                    file_id=getattr(args, 'file', None),
                    accounting_firm_id=accounting_firm_id
                )
                
                if args.json:
                    exibir_resultado_json(resultado)
                else:
                    status = resultado.get("status", "N/A")
                    status_code = resultado.get("status_code", "N/A")
                    file_size = resultado.get("file_size", 0)
                    content_type = resultado.get("content_type", "N/A")
                    file_id = resultado.get("file_id", "N/A")
                    
                    if status == "success":
                        print("Upload realizado com sucesso!")
                        print(f"Status HTTP: {status_code}")
                        print(f"Arquivo: {resultado.get('file_path', 'N/A')}")
                        print(f"Tamanho: {file_size} bytes")
                        print(f"Content-Type: {content_type}")
                        print(f"ID do arquivo: {file_id}")
                        
                        conferencia = resultado.get("conferencia", {})
                        if conferencia:
                            conf_status = conferencia.get("status", "N/A")
                            if conf_status == "success":
                                print("\nArquivo enviado para conferência com sucesso!")
                            else:
                                erro = conferencia.get("erro", "Erro desconhecido")
                                print(f"\nAVISO: Erro ao enviar para conferência: {erro}")
                    else:
                        print(f"ERRO no upload. Status HTTP: {status_code}")
            except Exception as e:
                print(f"ERRO ao fazer upload: {e}")
                if args.json:
                    import traceback
                    traceback.print_exc()
                return 1
    
    except Exception as e:
        print(f"ERRO: {e}")
        if args.json:
            import traceback
            traceback.print_exc()
        return 1
    
    return 0

