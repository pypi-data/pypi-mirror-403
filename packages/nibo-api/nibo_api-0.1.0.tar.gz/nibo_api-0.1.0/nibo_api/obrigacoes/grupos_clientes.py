"""
Interface para grupos de clientes no Nibo Obrigações
"""
from typing import Optional, Dict, Any
from uuid import UUID

from nibo_api.common.client import BaseClient


class GruposClientesInterface:
    """Interface para operações com grupos de clientes"""
    
    def __init__(self, client: BaseClient):
        """
        Inicializa a interface de grupos de clientes
        
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
        Lista todos os grupos de clientes de um escritório
        
        Args:
            accounting_firm_id: UUID do escritório contábil
            odata_filter: Filtro OData
            odata_orderby: Campo para ordenação
            odata_top: Limite de registros
            odata_skip: Registros a pular
            
        Returns:
            Dicionário com 'items' (lista de grupos) e 'metadata'
        """
        return self.client.get(
            f"/accountingfirms/{accounting_firm_id}/tags",
            odata_filter=odata_filter,
            odata_orderby=odata_orderby,
            odata_top=odata_top,
            odata_skip=odata_skip
        )

