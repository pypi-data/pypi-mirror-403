"""
Interface para gerenciamento de organizações no Nibo Empresa
"""
from typing import Optional, Dict, Any

from nibo_api.common.client import BaseClient


class OrganizacoesInterface:
    """Interface para operações com organizações"""
    
    def __init__(self, client: BaseClient):
        """
        Inicializa a interface de organizações
        
        Args:
            client: Instância do cliente HTTP base
        """
        self.client = client
    
    def listar_organizacoes(
        self,
        odata_filter: Optional[str] = None,
        odata_orderby: Optional[str] = None,
        odata_top: Optional[int] = None,
        odata_skip: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Lista todas as organizações que o usuário administrador tem acesso
        
        Args:
            odata_filter: Filtro OData
            odata_orderby: Campo para ordenação
            odata_top: Limite de registros
            odata_skip: Registros a pular
            
        Returns:
            Dicionário com lista de organizações
        """
        return self.client.get(
            "/organizations",
            odata_filter=odata_filter,
            odata_orderby=odata_orderby,
            odata_top=odata_top,
            odata_skip=odata_skip
        )
    
    def listar_usuarios(
        self,
        odata_filter: Optional[str] = None,
        odata_orderby: Optional[str] = None,
        odata_top: Optional[int] = None,
        odata_skip: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Lista usuários da organização
        
        Args:
            odata_filter: Filtro OData
            odata_orderby: Campo para ordenação
            odata_top: Limite de registros
            odata_skip: Registros a pular
            
        Returns:
            Dicionário com 'items' (lista de usuários) e 'count' (total)
        """
        return self.client.get(
            "/users",
            odata_filter=odata_filter,
            odata_orderby=odata_orderby,
            odata_top=odata_top,
            odata_skip=odata_skip
        )

