"""
Interface para agendamentos de pagamento no Nibo Empresa
"""
from typing import Optional, Dict, Any
from uuid import UUID

from nibo_api.common.client import BaseClient


class AgendamentosPagarInterface:
    """Interface para operações com agendamentos de pagamento"""
    
    def __init__(self, client: BaseClient):
        """
        Inicializa a interface de agendamentos de pagamento
        
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
        Lista pagamentos agendados em aberto (contas a pagar)
        
        Args:
            odata_filter: Filtro OData
            odata_orderby: Campo para ordenação
            odata_top: Limite de registros
            odata_skip: Registros a pular
            
        Returns:
            Dicionário com 'items' (lista de agendamentos) e 'count' (total)
        """
        return self.client.get(
            "/schedules/debit/opened",
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
        Lista pagamentos agendados vencidos
        
        Args:
            odata_filter: Filtro OData
            odata_orderby: Campo para ordenação
            odata_top: Limite de registros
            odata_skip: Registros a pular
            
        Returns:
            Dicionário com 'items' (lista de agendamentos) e 'count' (total)
        """
        return self.client.get(
            "/schedules/debit/dued",
            odata_filter=odata_filter,
            odata_orderby=odata_orderby,
            odata_top=odata_top,
            odata_skip=odata_skip
        )
    
    def agendar(
        self,
        categories: list,
        stakeholder_id: UUID,
        schedule_date: str,
        due_date: str,
        description: str,
        reference: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Agenda um novo pagamento
        
        Args:
            categories: Lista de categorias com categoryId, value e description
            stakeholder_id: UUID do stakeholder (fornecedor)
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
        
        return self.client.post("/schedules/debit", json_data=payload)
    
    def agendar_json(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Agenda um pagamento usando payload JSON completo
        
        Args:
            payload: Dicionário completo com dados do agendamento
            
        Returns:
            Dados do agendamento criado
        """
        return self.client.post("/schedules/debit", json_data=payload)
    
    def pagar_lancamento_agendado(
        self,
        schedule_id: UUID,
        payment_date: str,
        value: Optional[float] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Paga um lançamento agendado (marca como pago)
        
        Args:
            schedule_id: UUID do agendamento
            payment_date: Data do pagamento (formato: DD/MM/YYYY)
            value: Valor a pagar (opcional, se não informado paga o valor total)
            **kwargs: Outros campos opcionais
            
        Returns:
            Dados do pagamento
        """
        payload = {
            "paymentDate": payment_date
        }
        
        if value is not None:
            payload["value"] = value
        
        payload.update(kwargs)
        
        return self.client.post(f"/schedules/debit/{schedule_id}/pay", json_data=payload)
    
    def atualizar(
        self,
        schedule_id: UUID,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Atualiza um agendamento de pagamento
        
        Args:
            schedule_id: UUID do agendamento
            **kwargs: Campos a atualizar
            
        Returns:
            Dados do agendamento atualizado
        """
        return self.client.put(
            f"/schedules/debit/{schedule_id}",
            json_data=kwargs
        )
    
    def excluir(self, schedule_id: UUID) -> Dict[str, Any]:
        """
        Exclui um agendamento de pagamento
        
        Args:
            schedule_id: UUID do agendamento
            
        Returns:
            Resposta da API
        """
        return self.client.delete(f"/schedules/debit/{schedule_id}")

