"""
Interface para upload de arquivos no Nibo Empresa
"""
from typing import Optional, Dict, Any
from uuid import UUID
from pathlib import Path

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
    
    def upload(
        self,
        file_path: str,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Faz upload de um arquivo
        
        Args:
            file_path: Caminho do arquivo a fazer upload
            description: Descrição do arquivo (opcional)
            
        Returns:
            Dados do arquivo enviado
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")
        
        with open(path, 'rb') as f:
            files = {'file': (path.name, f, 'application/octet-stream')}
            data = {}
            if description:
                data['description'] = description
            
            # Usa requests diretamente para upload de arquivo
            import requests
            url = f"{self.client.base_url}/files"
            # Usa os headers da sessão que já contém o token correto
            headers = self.client.session.headers.copy()
            
            response = requests.post(url, files=files, data=data, headers=headers)
            return self.client._handle_response(response)

