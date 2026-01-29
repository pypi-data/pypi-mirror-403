"""
Interface para parcelamentos no Nibo Empresa
"""
from typing import Optional, Dict, Any
from uuid import UUID

from nibo_api.common.client import BaseClient


class ParcelamentosInterface:
    """Interface para operações com parcelamentos"""
    
    def __init__(self, client: BaseClient):
        """
        Inicializa a interface de parcelamentos
        
        Args:
            client: Instância do cliente HTTP base
        """
        self.client = client
    
    def listar_agendamentos_parcelamento(
        self,
        parcelamento_id: UUID,
        odata_filter: Optional[str] = None,
        odata_orderby: Optional[str] = None,
        odata_top: Optional[int] = None,
        odata_skip: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Lista agendamentos de um parcelamento
        
        Args:
            parcelamento_id: UUID do parcelamento
            odata_filter: Filtro OData
            odata_orderby: Campo para ordenação
            odata_top: Limite de registros
            odata_skip: Registros a pular
            
        Returns:
            Dicionário com 'items' (lista de agendamentos) e 'count' (total)
        """
        return self.client.get(
            f"/installments/{parcelamento_id}/schedules",
            odata_filter=odata_filter,
            odata_orderby=odata_orderby,
            odata_top=odata_top,
            odata_skip=odata_skip
        )
    
    def buscar_por_id(self, parcelamento_id: UUID) -> Dict[str, Any]:
        """
        Busca um parcelamento por ID
        
        Args:
            parcelamento_id: UUID do parcelamento
            
        Returns:
            Dados do parcelamento
        """
        return self.client.get(f"/installments/{parcelamento_id}")

