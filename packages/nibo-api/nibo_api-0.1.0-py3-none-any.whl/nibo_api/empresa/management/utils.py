"""
Funções utilitárias para comandos CLI de empresa
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


def exibir_agendamentos(agendamentos: Dict[str, Any], tipo: str = "receber"):
    """
    Exibe agendamentos em formato tabular
    
    Args:
        agendamentos: Dicionário retornado por listar_agendamentos_*
        tipo: Tipo de agendamento ('receber' ou 'pagar')
    """
    items = agendamentos.get("items", [])
    total = len(items)
    
    print("=" * 100)
    tipo_nome = "RECEBIMENTOS" if tipo == "receber" else "PAGAMENTOS"
    print(f"AGENDAMENTOS DE {tipo_nome}")
    print(f"Total: {total} agendamento(s)")
    print("=" * 100)
    print()
    
    if total > 0:
        print(f"{'Data Venc.':<12} {'Data Agend.':<12} {'Valor':<15} {'Cliente/Fornec.':<30} {'Descrição':<30}")
        print("-" * 100)
        
        for item in items:
            # Data de vencimento
            due_date = item.get("dueDate")
            due_date_str = format_date(parse_date(due_date)) if due_date else "N/A"
            
            # Data de agendamento
            schedule_date = item.get("scheduleDate")
            schedule_date_str = format_date(parse_date(schedule_date)) if schedule_date else "N/A"
            
            # Valor
            value = item.get("value", 0)
            try:
                value_str = f"R$ {float(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            except:
                value_str = str(value) if value else "N/A"
            
            # Cliente/Fornecedor
            stakeholder = item.get("stakeholder", {})
            stakeholder_name = stakeholder.get("name", "N/A") if isinstance(stakeholder, dict) else "N/A"
            stakeholder_display = stakeholder_name[:28] + "..." if len(stakeholder_name) > 30 else stakeholder_name
            
            # Descrição
            description = item.get("description", "N/A")
            description_display = description[:28] + "..." if len(description) > 30 else description
            
            print(f"{due_date_str:<12} {schedule_date_str:<12} {value_str:<15} {stakeholder_display:<30} {description_display:<30}")
            
            # Informações adicionais
            reference = item.get("reference")
            if reference:
                print(f"   Referência: {reference}")
            
            item_id = item.get("id", "N/A")
            print(f"   ID: {item_id}")
        
        print("-" * 100)
        print(f"Total: {total} agendamento(s)")
    else:
        print("Nenhum agendamento encontrado.")


