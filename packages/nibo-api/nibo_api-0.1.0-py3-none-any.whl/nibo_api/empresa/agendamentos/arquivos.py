"""
Interface para arquivos de agendamentos no Nibo Empresa
"""
from typing import Optional, Dict, Any
from uuid import UUID

from nibo_api.common.client import BaseClient


class ArquivosAgendamentoInterface:
    """Interface para operações com arquivos de agendamentos"""
    
    def __init__(self, client: BaseClient):
        """
        Inicializa a interface de arquivos de agendamentos
        
        Args:
            client: Instância do cliente HTTP base
        """
        self.client = client
    
    def buscar_por_agendamento(
        self,
        schedule_id: UUID
    ) -> Dict[str, Any]:
        """
        Busca arquivos por ID do agendamento
        
        Args:
            schedule_id: UUID do agendamento
            
        Returns:
            Lista de arquivos do agendamento
        """
        return self.client.get(f"/schedules/{schedule_id}/files")
    
    def anexar_recebimento(
        self,
        schedule_id: UUID,
        file_id: UUID
    ) -> Dict[str, Any]:
        """
        Anexa arquivo no agendamento de recebimento
        
        Args:
            schedule_id: UUID do agendamento
            file_id: UUID do arquivo
            
        Returns:
            Resposta da API
        """
        payload = {
            "fileId": str(file_id)
        }
        
        return self.client.post(
            f"/schedules/credit/{schedule_id}/files",
            json_data=payload
        )
    
    def excluir_recebimento(
        self,
        schedule_id: UUID,
        file_id: UUID
    ) -> Dict[str, Any]:
        """
        Exclui arquivo do agendamento de recebimento
        
        Args:
            schedule_id: UUID do agendamento
            file_id: UUID do arquivo
            
        Returns:
            Resposta da API
        """
        return self.client.delete(
            f"/schedules/credit/{schedule_id}/files/{file_id}"
        )
    
    def anexar_pagamento(
        self,
        schedule_id: UUID,
        file_id: UUID
    ) -> Dict[str, Any]:
        """
        Anexa arquivo no agendamento de pagamento
        
        Args:
            schedule_id: UUID do agendamento
            file_id: UUID do arquivo
            
        Returns:
            Resposta da API
        """
        payload = {
            "fileId": str(file_id)
        }
        
        return self.client.post(
            f"/schedules/debit/{schedule_id}/files",
            json_data=payload
        )
    
    def excluir_pagamento(
        self,
        schedule_id: UUID,
        file_id: UUID
    ) -> Dict[str, Any]:
        """
        Exclui arquivo do agendamento de pagamento
        
        Args:
            schedule_id: UUID do agendamento
            file_id: UUID do arquivo
            
        Returns:
            Resposta da API
        """
        return self.client.delete(
            f"/schedules/debit/{schedule_id}/files/{file_id}"
        )

