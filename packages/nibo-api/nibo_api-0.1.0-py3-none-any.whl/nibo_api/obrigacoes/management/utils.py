"""
Funções utilitárias para comandos CLI de obrigações
"""
import json
from datetime import datetime, date
from typing import Dict, Any


def parse_date(date_str):
    """Parse uma data de string para objeto date"""
    if not date_str or date_str == "N/A":
        return None
    try:
        date_str = str(date_str).strip()
        # Tenta formato DD/MM/YYYY primeiro
        if "/" in date_str:
            parts = date_str.split("/")
            if len(parts) == 3:
                return date(int(parts[2]), int(parts[1]), int(parts[0]))
        # Tenta formato ISO (YYYY-MM-DD ou YYYY-MM-DDTHH:MM:SS)
        date_str = date_str.split("T")[0].replace("Z", "")
        return datetime.fromisoformat(date_str).date()
    except:
        return None


def format_date(date_obj):
    """Formata uma data para exibição"""
    if isinstance(date_obj, date):
        return date_obj.strftime("%d/%m/%Y")
    return str(date_obj)


def exibir_resultado_json(resultado: Dict[str, Any]):
    """Exibe resultado em formato JSON"""
    print(json.dumps(resultado, indent=2, ensure_ascii=False, default=str))


def exibir_lista_simples(resultado: Dict[str, Any], campo_nome: str = "name"):
    """Exibe lista simples de itens"""
    items = resultado.get("items", [])
    if not items:
        print("Nenhum item encontrado.")
        return
    
    print(f"Total: {len(items)} item(ns)")
    print("-" * 80)
    for i, item in enumerate(items, 1):
        nome = item.get(campo_nome, item.get("id", "N/A"))
        item_id = item.get("id", "N/A")
        print(f"{i}. {nome} (ID: {item_id})")


def exibir_obrigacoes(obrigacoes: Dict[str, Any], detalhado: bool = True):
    """
    Exibe obrigações em formato tabular
    
    Args:
        obrigacoes: Dicionário retornado por listar_obrigacoes_cliente()
        detalhado: Se True, exibe informações detalhadas
    """
    items = obrigacoes.get("items", [])
    total = obrigacoes.get("total_periodo", 0)
    clientes_info = obrigacoes.get("clientes_info", [])
    total_clientes = obrigacoes.get("total_clientes", len(clientes_info) if clientes_info else 0)
    periodo = obrigacoes.get("periodo", {})
    
    print("=" * 100)
    if total_clientes == 1:
        print(f"OBRIGAÇÕES - {clientes_info[0].get('name', 'N/A')}")
    else:
        nomes_clientes = [c.get('name', 'N/A') for c in clientes_info]
        print(f"OBRIGAÇÕES - {total_clientes} cliente(s): {', '.join(nomes_clientes[:3])}")
        if total_clientes > 3:
            print(f"  ... e mais {total_clientes - 3} cliente(s)")
    if periodo:
        print(f"Período: {format_date(periodo.get('inicio'))} até {format_date(periodo.get('fim'))}")
    print(f"Total no período: {total} obrigação(ões)")
    print("=" * 100)
    print()
    
    if total > 0:
        print(f"{'Data Venc.':<12} {'Competência':<12} {'Data Protocolo':<20} {'Status':<20} {'Tipo':<15} {'Valor':<15}")
        print("-" * 100)
        
        for item in items:
            # Data de vencimento
            duedate = item.get("dueDate")
            duedate_obj = parse_date(duedate) if duedate else None
            duedate_str = format_date(duedate_obj) if duedate_obj else (duedate if duedate else "N/A")
            
            # Competência
            accrual = item.get("accrual")
            if accrual:
                if isinstance(accrual, (int, float)):
                    accrual_str = str(int(accrual))
                else:
                    accrual_str = str(accrual)
            else:
                accrual_str = "N/A"
            
            # Data do protocolo
            fileddate = item.get("filedDate")
            fileddate_obj = parse_date(fileddate) if fileddate else None
            fileddate_str = format_date(fileddate_obj) if fileddate_obj else (fileddate if fileddate else "N/A")
            
            # Status
            status_type = item.get("status") or item.get("statusType")
            status_map = {
                1: "Excluído",
                2: "Cancelado",
                3: "Não Recebido",
                4: "Recebido",
                5: "Baixa Justificada",
                6: "Pago"
            }
            status = status_map.get(status_type, f"Status {status_type}" if status_type is not None else "N/A")
            
            # Tipo de obrigação
            obligation = item.get("obligation", {})
            obligation_type = obligation.get("type") if isinstance(obligation, dict) else None
            tipo_map = {
                1: "Pagamento",
                2: "Cadastral",
                3: "Declaração",
                4: "Diversos"
            }
            tipo = tipo_map.get(obligation_type, f"Tipo {obligation_type}" if obligation_type is not None else "N/A")
            
            # Valor
            value = item.get("value")
            if value is not None:
                try:
                    value_str = f"R$ {float(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                except:
                    value_str = str(value) if value else "N/A"
            else:
                value_str = "N/A"
            
            print(f"{duedate_str:<12} {accrual_str:<12} {fileddate_str:<20} {status:<20} {tipo:<15} {value_str:<15}")
            
            if detalhado:
                # Informações detalhadas
                number = item.get("number", "N/A")
                obligation_name = obligation.get("name", "N/A") if isinstance(obligation, dict) else "N/A"
                department = item.get("department", {})
                department_name = department.get("name", "N/A") if isinstance(department, dict) else "N/A"
                
                destination_type = item.get("destinationType")
                destination_map = {
                    1: "Arquivos Online",
                    2: "Controle Interno",
                    3: "Cliente",
                    4: "Contador",
                    5: "Baixa Justificada"
                }
                destination = destination_map.get(destination_type, f"Destino {destination_type}" if destination_type is not None else "N/A")
                
                print(f"   Número: {number} | Obrigação: {obligation_name} | Departamento: {department_name}")
                print(f"   Destino: {destination}")
        
        print("-" * 100)
        print(f"Total: {total} obrigação(ões)")
    else:
        print("Nenhuma obrigação encontrada no período especificado.")


