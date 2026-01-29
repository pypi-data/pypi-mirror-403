"""
Interface para conciliação no Nibo Empresa
"""
from typing import Optional, Dict, Any
from uuid import UUID

from nibo_api.common.client import BaseClient


class ConciliacaoInterface:
    """Interface para operações de conciliação"""
    
    def __init__(self, client: BaseClient):
        """
        Inicializa a interface de conciliação
        
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
        Lista conciliações
        
        Args:
            odata_filter: Filtro OData
            odata_orderby: Campo para ordenação
            odata_top: Limite de registros
            odata_skip: Registros a pular
            
        Returns:
            Dicionário com 'items' (lista de conciliações) e 'count' (total)
        """
        return self.client.get(
            "/reconciliations",
            odata_filter=odata_filter,
            odata_orderby=odata_orderby,
            odata_top=odata_top,
            odata_skip=odata_skip
        )
    
    def excluir(self, conciliacao_id: UUID) -> Dict[str, Any]:
        """
        Exclui uma conciliação
        
        Args:
            conciliacao_id: UUID da conciliação
            
        Returns:
            Resposta da API
        """
        return self.client.delete(f"/reconciliations/{conciliacao_id}")

