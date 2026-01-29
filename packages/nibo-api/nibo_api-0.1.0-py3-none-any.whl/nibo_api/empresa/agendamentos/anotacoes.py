"""
Interface para anotações de agendamentos no Nibo Empresa
"""
from typing import Optional, Dict, Any
from uuid import UUID

from nibo_api.common.client import BaseClient


class AnotacoesAgendamentoInterface:
    """Interface para operações com anotações de agendamentos"""
    
    def __init__(self, client: BaseClient):
        """
        Inicializa a interface de anotações de agendamentos
        
        Args:
            client: Instância do cliente HTTP base
        """
        self.client = client
    
    def listar(
        self,
        schedule_id: UUID,
        odata_filter: Optional[str] = None,
        odata_orderby: Optional[str] = None,
        odata_top: Optional[int] = None,
        odata_skip: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Lista anotações de um agendamento
        
        Args:
            schedule_id: UUID do agendamento
            odata_filter: Filtro OData
            odata_orderby: Campo para ordenação
            odata_top: Limite de registros
            odata_skip: Registros a pular
            
        Returns:
            Dicionário com 'items' (lista de anotações) e 'count' (total)
        """
        return self.client.get(
            f"/schedules/{schedule_id}/notes",
            odata_filter=odata_filter,
            odata_orderby=odata_orderby,
            odata_top=odata_top,
            odata_skip=odata_skip
        )
    
    def criar(
        self,
        schedule_id: UUID,
        text: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Cria uma nova anotação
        
        Args:
            schedule_id: UUID do agendamento
            text: Texto da anotação
            **kwargs: Outros campos opcionais
            
        Returns:
            Dados da anotação criada
        """
        payload = {
            "text": text
        }
        payload.update(kwargs)
        
        return self.client.post(
            f"/schedules/{schedule_id}/notes",
            json_data=payload
        )
    
    def excluir(
        self,
        schedule_id: UUID,
        note_id: UUID
    ) -> Dict[str, Any]:
        """
        Exclui uma anotação
        
        Args:
            schedule_id: UUID do agendamento
            note_id: UUID da anotação
            
        Returns:
            Resposta da API
        """
        return self.client.delete(
            f"/schedules/{schedule_id}/notes/{note_id}"
        )

