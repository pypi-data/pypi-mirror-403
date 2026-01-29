"""
Interface para conferência no Nibo Obrigações
"""
from typing import Optional, Dict, Any
from uuid import UUID

from nibo_api.common.client import BaseClient


class ConferenciaInterface:
    """Interface para operações de conferência"""
    
    def __init__(self, client: BaseClient):
        """
        Inicializa a interface de conferência
        
        Args:
            client: Instância do cliente HTTP base
        """
        self.client = client
    
    def enviar_tela_conferencia(
        self,
        accounting_firm_id: UUID,
        task_id: UUID,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Envia para tela de conferência
        
        Args:
            accounting_firm_id: UUID do escritório contábil
            task_id: UUID da tarefa
            **kwargs: Outros campos opcionais
            
        Returns:
            Resposta da API
        """
        payload = {
            "taskId": str(task_id)
        }
        payload.update(kwargs)
        
        return self.client.post(
            f"/accountingfirms/{accounting_firm_id}/conference",
            json_data=payload
        )
    
    def enviar_arquivo_conferencia(
        self,
        accounting_firm_id: UUID,
        file_id: UUID,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Envia um arquivo para a tela de conferência
        
        IMPORTANTE: Antes de enviar para conferência, é necessário:
        1. Criar o arquivo usando arquivos.criar_arquivo_upload()
        2. Fazer upload do arquivo usando arquivos.fazer_upload()
        3. Então enviar para conferência usando este método
        
        Args:
            accounting_firm_id: UUID do escritório contábil
            file_id: UUID do arquivo (retornado após criar e fazer upload)
            **kwargs: Outros campos opcionais
            
        Returns:
            Resposta da API
        """
        payload = {
            "fileId": str(file_id)
        }
        payload.update(kwargs)
        
        return self.client.post(
            f"/accountingfirms/{accounting_firm_id}/conferences",
            json_data=payload
        )

