"""
Interface para tarefas no Nibo Obrigações
"""
from typing import Optional, Dict, Any, List
from uuid import UUID

from nibo_api.common.client import BaseClient


# Constantes para Status
STATUS_UNDEFINED = 0
STATUS_BLOCKED = 1
STATUS_TODO = 2
STATUS_COMPLETE = 3

# Constantes para SkipHoliday
SKIP_HOLIDAY_NONE = 0
SKIP_HOLIDAY_ANTECIPAR = 1
SKIP_HOLIDAY_POSTERGAR = 2
SKIP_HOLIDAY_INVALIDO = 3

# Constantes para Frequency
FREQUENCY_NONE = 0
FREQUENCY_DAILY = 1
FREQUENCY_WEEKLY = 2
FREQUENCY_MONTHLY = 3
FREQUENCY_YEARLY = 4

# Constantes para FrequencySchedule (dias da semana)
FREQ_SCHEDULE_NONE = 0
FREQ_SCHEDULE_SUNDAY = 1
FREQ_SCHEDULE_MONDAY = 2
FREQ_SCHEDULE_TUESDAY = 4
FREQ_SCHEDULE_WEDNESDAY = 8
FREQ_SCHEDULE_THURSDAY = 16
FREQ_SCHEDULE_FRIDAY = 32
FREQ_SCHEDULE_SATURDAY = 64


def interpretar_status(status: int) -> str:
    """
    Interpreta o valor do status de uma tarefa
    
    Args:
        status: Valor numérico do status
        
    Returns:
        Descrição do status
    """
    status_map = {
        STATUS_UNDEFINED: "Undefined",
        STATUS_BLOCKED: "Blocked",
        STATUS_TODO: "ToDo",
        STATUS_COMPLETE: "Complete"
    }
    return status_map.get(status, f"Status desconhecido ({status})")


def interpretar_skip_holiday(skip_holiday: int) -> str:
    """
    Interpreta o valor de SkipHoliday
    
    Args:
        skip_holiday: Valor numérico de SkipHoliday
        
    Returns:
        Descrição da regra
    """
    skip_map = {
        SKIP_HOLIDAY_NONE: "Nenhuma regra",
        SKIP_HOLIDAY_ANTECIPAR: "Antecipar para dia útil anterior",
        SKIP_HOLIDAY_POSTERGAR: "Postergar para próximo dia útil",
        SKIP_HOLIDAY_INVALIDO: "Data inválida se for feriado/fim de semana"
    }
    return skip_map.get(skip_holiday, f"Regra desconhecida ({skip_holiday})")


def interpretar_frequency(frequency: int) -> str:
    """
    Interpreta o valor de Frequency
    
    Args:
        frequency: Valor numérico de Frequency
        
    Returns:
        Descrição da frequência
    """
    freq_map = {
        FREQUENCY_NONE: "Sem recorrência",
        FREQUENCY_DAILY: "Recorrência diária",
        FREQUENCY_WEEKLY: "Recorrência semanal",
        FREQUENCY_MONTHLY: "Recorrência mensal",
        FREQUENCY_YEARLY: "Recorrência anual"
    }
    return freq_map.get(frequency, f"Frequência desconhecida ({frequency})")


def interpretar_frequency_schedule(schedule: int) -> list:
    """
    Interpreta o valor de FrequencySchedule (flags de dias da semana)
    
    Args:
        schedule: Valor numérico de FrequencySchedule (pode ser combinação de flags)
        
    Returns:
        Lista de dias da semana selecionados
    """
    dias = []
    if schedule & FREQ_SCHEDULE_SUNDAY:
        dias.append("Domingo")
    if schedule & FREQ_SCHEDULE_MONDAY:
        dias.append("Segunda-feira")
    if schedule & FREQ_SCHEDULE_TUESDAY:
        dias.append("Terça-feira")
    if schedule & FREQ_SCHEDULE_WEDNESDAY:
        dias.append("Quarta-feira")
    if schedule & FREQ_SCHEDULE_THURSDAY:
        dias.append("Quinta-feira")
    if schedule & FREQ_SCHEDULE_FRIDAY:
        dias.append("Sexta-feira")
    if schedule & FREQ_SCHEDULE_SATURDAY:
        dias.append("Sábado")
    
    return dias if dias else ["Nenhum dia selecionado"]


class TarefasInterface:
    """Interface para operações com tarefas"""
    
    def __init__(self, client: BaseClient):
        """
        Inicializa a interface de tarefas
        
        Args:
            client: Instância do cliente HTTP base
        """
        self.client = client
    
    def listar(
        self,
        accounting_firm_id: UUID,
        odata_filter: Optional[str] = None,
        odata_orderby: Optional[str] = None,
        odata_top: Optional[int] = None,
        odata_skip: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Lista todas as tarefas de um escritório
        
        Args:
            accounting_firm_id: UUID do escritório contábil
            odata_filter: Filtro OData
            odata_orderby: Campo para ordenação
            odata_top: Limite de registros
            odata_skip: Registros a pular
            
        Returns:
            Dicionário com 'items' (lista de tarefas) e 'metadata'
        """
        return self.client.get(
            f"/accountingfirms/{accounting_firm_id}/tasks",
            odata_filter=odata_filter,
            odata_orderby=odata_orderby,
            odata_top=odata_top,
            odata_skip=odata_skip
        )
    
    def criar(
        self,
        accounting_firm_id: UUID,
        name: str,
        task_template_id: Optional[str] = None,
        deadline: Optional[str] = None,
        in_charge_user_id: Optional[str] = None,
        is_department_customer_representative: Optional[bool] = None,
        customer_id: Optional[str] = None,
        description: Optional[str] = None,
        department_id: Optional[str] = None,
        file_ids: Optional[List[str]] = None,
        check_lists: Optional[List[Dict[str, Any]]] = None,
        follower_ids: Optional[List[str]] = None,
        notes: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Cria uma nova tarefa
        
        Args:
            accounting_firm_id: UUID do escritório contábil
            name: Nome da tarefa (obrigatório, exceto quando usar template)
            task_template_id: ID do template para criar tarefa a partir de template (opcional)
            deadline: Data e hora limite para conclusão (formato: YYYY-MM-DDTHH:MM:SS)
            in_charge_user_id: ID do usuário responsável (opcional)
            is_department_customer_representative: Se o departamento é representante do cliente (opcional)
            customer_id: ID do cliente associado (opcional)
            description: Descrição da tarefa (opcional)
            department_id: ID do departamento relacionado (opcional)
            file_ids: Lista de IDs de arquivos anexados (opcional)
            check_lists: Lista de subtarefas com título e posição (opcional)
            follower_ids: IDs dos usuários que acompanham a tarefa (opcional)
            notes: Anotações com arquivos relacionados (opcional)
            **kwargs: Outros campos opcionais
            
        Returns:
            Resposta da API (status 202 Accepted - criação assíncrona)
            
        Note:
            - Se task_template_id for fornecido, a tarefa será criada a partir do template
            - O campo 'name' não pode ser modificado quando usar template
            - A API retorna status 202 (Accepted) indicando criação assíncrona
        """
        payload = {}
        
        # Se não usar template, name é obrigatório
        if not task_template_id:
            payload["name"] = name
        
        # Adiciona campos opcionais se fornecidos
        if task_template_id:
            payload["taskTemplateId"] = task_template_id
        if deadline:
            payload["deadLine"] = deadline
        if in_charge_user_id:
            payload["inChargeUserId"] = in_charge_user_id
        if is_department_customer_representative is not None:
            payload["isDepartmentCustomerRepresentative"] = is_department_customer_representative
        if customer_id:
            payload["customerId"] = customer_id
        if description:
            payload["description"] = description
        if department_id:
            payload["departmentId"] = department_id
        if file_ids:
            payload["fileIds"] = file_ids
        if check_lists:
            payload["checkLists"] = check_lists
        if follower_ids:
            payload["followerIds"] = follower_ids
        if notes:
            payload["notes"] = notes
        
        # Adiciona outros campos de kwargs
        payload.update(kwargs)
        
        return self.client.post(
            f"/accountingfirms/{accounting_firm_id}/tasks",
            json_data=payload
        )

