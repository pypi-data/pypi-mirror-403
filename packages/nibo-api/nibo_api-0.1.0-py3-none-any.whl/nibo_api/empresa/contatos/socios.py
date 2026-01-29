"""
Interface para gerenciamento de sócios no Nibo Empresa
"""
from typing import Optional, Dict, Any
from uuid import UUID

from nibo_api.common.client import BaseClient


class SociosInterface:
    """Interface para operações com sócios"""
    
    def __init__(self, client: BaseClient):
        """
        Inicializa a interface de sócios
        
        Args:
            client: Instância do cliente HTTP base
        """
        self.client = client
    
    def listar(
        self,
        odata_filter: Optional[str] = None,
        odata_orderby: Optional[str] = None,
        odata_top: Optional[int] = None,
        odata_skip: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Lista todos os sócios
        
        Args:
            odata_filter: Filtro OData
            odata_orderby: Campo para ordenação
            odata_top: Limite de registros
            odata_skip: Registros a pular
            
        Returns:
            Dicionário com 'items' (lista de sócios) e 'count' (total)
        """
        return self.client.get(
            "/partners",
            odata_filter=odata_filter,
            odata_orderby=odata_orderby,
            odata_top=odata_top,
            odata_skip=odata_skip
        )
    
    def buscar_agendamentos_por_socio(
        self,
        socio_id: UUID,
        odata_filter: Optional[str] = None,
        odata_orderby: Optional[str] = None,
        odata_top: Optional[int] = None,
        odata_skip: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Busca agendamentos de um sócio específico
        
        Args:
            socio_id: UUID do sócio
            odata_filter: Filtro OData
            odata_orderby: Campo para ordenação
            odata_top: Limite de registros
            odata_skip: Registros a pular
            
        Returns:
            Lista de agendamentos do sócio
        """
        return self.client.get(
            f"/partners/{socio_id}/schedules",
            odata_filter=odata_filter,
            odata_orderby=odata_orderby,
            odata_top=odata_top,
            odata_skip=odata_skip
        )
    
    def buscar_por_id(self, socio_id: UUID) -> Dict[str, Any]:
        """
        Busca um sócio por ID
        
        Args:
            socio_id: UUID do sócio
            
        Returns:
            Dados do sócio
        """
        return self.client.get(f"/partners/{socio_id}")
    
    def criar(
        self,
        name: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Cria um novo sócio
        
        Args:
            name: Nome do sócio
            **kwargs: Outros campos opcionais
            
        Returns:
            Dados do sócio criado
        """
        payload = {"name": name}
        payload.update(kwargs)
        
        return self.client.post("/partners/FormatType=json", json_data=payload)
    
    def atualizar(
        self,
        socio_id: UUID,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Atualiza um sócio existente
        
        Args:
            socio_id: UUID do sócio
            **kwargs: Campos a atualizar
            
        Returns:
            Dados do sócio atualizado
        """
        return self.client.put(
            f"/partners/{socio_id}",
            json_data=kwargs
        )
    
    def excluir(self, socio_id: UUID) -> Dict[str, Any]:
        """
        Exclui um sócio
        
        Args:
            socio_id: UUID do sócio
            
        Returns:
            Resposta da API
        """
        return self.client.delete(f"/partners/{socio_id}")

