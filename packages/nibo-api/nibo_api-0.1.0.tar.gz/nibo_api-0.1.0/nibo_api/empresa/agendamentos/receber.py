"""
Interface para agendamentos de recebimento no Nibo Empresa
"""
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime

from nibo_api.common.client import BaseClient
from nibo_api.common.models import AgendamentoRecebimento, AgendamentoList


class AgendamentosReceberInterface:
    """Interface para operações com agendamentos de recebimento"""
    
    def __init__(self, client: BaseClient):
        """
        Inicializa a interface de agendamentos de recebimento
        
        Args:
            client: Instância do cliente HTTP base
        """
        self.client = client
    
    def listar_abertos(
        self,
        odata_filter: Optional[str] = None,
        odata_orderby: Optional[str] = None,
        odata_top: Optional[int] = None,
        odata_skip: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Lista recebimentos agendados em aberto (contas a receber)
        
        Args:
            odata_filter: Filtro OData (ex: "stakeholder/cpfCnpj eq '11497110000127'")
            odata_orderby: Campo para ordenação
            odata_top: Limite de registros
            odata_skip: Registros a pular
            
        Returns:
            Dicionário com 'items' (lista de agendamentos) e 'count' (total)
        """
        return self.client.get(
            "/schedules/credit/opened",
            odata_filter=odata_filter,
            odata_orderby=odata_orderby,
            odata_top=odata_top,
            odata_skip=odata_skip
        )
    
    def listar_vencidos(
        self,
        odata_filter: Optional[str] = None,
        odata_orderby: Optional[str] = None,
        odata_top: Optional[int] = None,
        odata_skip: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Lista recebimentos agendados vencidos
        
        Args:
            odata_filter: Filtro OData
            odata_orderby: Campo para ordenação
            odata_top: Limite de registros
            odata_skip: Registros a pular
            
        Returns:
            Dicionário com 'items' (lista de agendamentos) e 'count' (total)
        """
        return self.client.get(
            "/schedules/credit/dued",
            odata_filter=odata_filter,
            odata_orderby=odata_orderby,
            odata_top=odata_top,
            odata_skip=odata_skip
        )
    
    def listar_todos(
        self,
        odata_filter: Optional[str] = None,
        odata_orderby: Optional[str] = None,
        odata_top: Optional[int] = None,
        odata_skip: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Lista todos os recebimentos agendados
        
        Args:
            odata_filter: Filtro OData
            odata_orderby: Campo para ordenação
            odata_top: Limite de registros
            odata_skip: Registros a pular
            
        Returns:
            Dicionário com 'items' (lista de agendamentos) e 'count' (total)
        """
        return self.client.get(
            "/schedules/credit",
            odata_filter=odata_filter,
            odata_orderby=odata_orderby,
            odata_top=odata_top,
            odata_skip=odata_skip
        )
    
    def buscar_por_agendamento(self, schedule_id: UUID) -> Dict[str, Any]:
        """
        Busca um recebimento por ID do agendamento
        
        Args:
            schedule_id: UUID do agendamento
            
        Returns:
            Dados do recebimento
        """
        return self.client.get(f"/schedules/credit/{schedule_id}")
    
    def agendar(
        self,
        categories: List[Dict[str, Any]],
        stakeholder_id: UUID,
        schedule_date: str,
        due_date: str,
        description: str,
        reference: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Agenda um novo recebimento
        
        Args:
            categories: Lista de categorias com categoryId, value e description
            stakeholder_id: UUID do stakeholder (cliente)
            schedule_date: Data de agendamento (formato: DD/MM/YYYY)
            due_date: Data de vencimento (formato: DD/MM/YYYY)
            description: Descrição do agendamento
            reference: Referência do agendamento (opcional)
            **kwargs: Outros campos opcionais
            
        Returns:
            Dados do agendamento criado
        """
        payload = {
            "categories": categories,
            "stakeholderId": str(stakeholder_id),
            "scheduleDate": schedule_date,
            "dueDate": due_date,
            "description": description
        }
        
        if reference:
            payload["reference"] = reference
        
        payload.update(kwargs)
        
        return self.client.post("/schedules/credit", json_data=payload)
    
    def agendar_json(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Agenda um recebimento usando payload JSON completo
        
        Args:
            payload: Dicionário completo com dados do agendamento
            
        Returns:
            Dados do agendamento criado
        """
        return self.client.post("/schedules/credit", json_data=payload)
    
    def receber_lancamento_agendado(
        self,
        schedule_id: UUID,
        payment_date: str,
        value: Optional[float] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Recebe um lançamento agendado (marca como pago)
        
        Args:
            schedule_id: UUID do agendamento
            payment_date: Data do pagamento (formato: DD/MM/YYYY)
            value: Valor a receber (opcional, se não informado recebe o valor total)
            **kwargs: Outros campos opcionais
            
        Returns:
            Dados do recebimento
        """
        payload = {
            "paymentDate": payment_date
        }
        
        if value is not None:
            payload["value"] = value
        
        payload.update(kwargs)
        
        return self.client.post(f"/schedules/credit/{schedule_id}/receive", json_data=payload)
    
    def atualizar(
        self,
        schedule_id: UUID,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Atualiza um agendamento de recebimento
        
        Args:
            schedule_id: UUID do agendamento
            **kwargs: Campos a atualizar
            
        Returns:
            Dados do agendamento atualizado
        """
        return self.client.put(
            f"/schedules/credit/{schedule_id}",
            json_data=kwargs
        )
    
    def excluir(self, schedule_id: UUID) -> Dict[str, Any]:
        """
        Exclui um agendamento de recebimento
        
        Args:
            schedule_id: UUID do agendamento
            
        Returns:
            Resposta da API
        """
        return self.client.delete(f"/schedules/credit/{schedule_id}")

