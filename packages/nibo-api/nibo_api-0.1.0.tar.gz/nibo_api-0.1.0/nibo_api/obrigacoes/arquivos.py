"""
Interface para arquivos no Nibo Obrigações
"""
from typing import Optional, Dict, Any
from uuid import UUID
import requests

from nibo_api.common.client import BaseClient


class ArquivosInterface:
    """Interface para operações com arquivos"""
    
    def __init__(self, client: BaseClient):
        """
        Inicializa a interface de arquivos
        
        Args:
            client: Instância do cliente HTTP base
        """
        self.client = client
    
    def criar_arquivo_upload(
        self,
        accounting_firm_id: UUID,
        name: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Cria arquivo para upload
        
        Retorna um dicionário com:
        - id: ID do arquivo criado
        - sharedAccessSignature: URL temporária válida por 10 minutos para fazer o upload
        
        IMPORTANTE: A URL sharedAccessSignature é válida por apenas 10 minutos.
        O upload deve ser concluído dentro desse período.
        
        Args:
            accounting_firm_id: UUID do escritório contábil
            name: Nome do arquivo
            **kwargs: Outros campos opcionais
            
        Returns:
            Dicionário com dados do arquivo criado, incluindo sharedAccessSignature
        """
        payload = {
            "name": name
        }
        payload.update(kwargs)
        
        return self.client.post(
            f"/accountingfirms/{accounting_firm_id}/files",
            json_data=payload
        )
    
    def fazer_upload(
        self,
        shared_access_signature: str,
        file_content: bytes,
        content_type: Optional[str] = None
    ) -> requests.Response:
        """
        Faz upload do arquivo usando a URL do sharedAccessSignature
        
        IMPORTANTE: A URL sharedAccessSignature é válida por apenas 10 minutos.
        O upload deve ser concluído dentro desse período.
        
        Args:
            shared_access_signature: URL retornada no campo sharedAccessSignature
            file_content: Conteúdo do arquivo em bytes
            content_type: Tipo MIME do arquivo (opcional)
            
        Returns:
            Resposta da requisição PUT
        """
        headers = {
            "x-ms-blob-type": "BlockBlob"
        }
        
        if content_type:
            headers["Content-Type"] = content_type
        
        # Faz PUT diretamente na URL do sharedAccessSignature
        response = requests.put(
            shared_access_signature,
            data=file_content,
            headers=headers
        )
        response.raise_for_status()
        return response

