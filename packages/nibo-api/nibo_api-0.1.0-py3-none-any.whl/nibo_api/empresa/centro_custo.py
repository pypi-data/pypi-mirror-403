"""
Interface para gerenciamento de centro de custo no Nibo Empresa
"""
from typing import Optional, Dict, Any
from uuid import UUID

from nibo_api.common.client import BaseClient


class CentroCustoInterface:
    """Interface para operações com centro de custo"""
    
    def __init__(self, client: BaseClient):
        """
        Inicializa a interface de centro de custo
        
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
        Lista todos os centros de custo
        
        Args:
            odata_filter: Filtro OData
            odata_orderby: Campo para ordenação
            odata_top: Limite de registros
            odata_skip: Registros a pular
            
        Returns:
            Dicionário com 'items' (lista de centros de custo) e 'count' (total)
        """
        return self.client.get(
            "/costcenters",
            odata_filter=odata_filter,
            odata_orderby=odata_orderby,
            odata_top=odata_top,
            odata_skip=odata_skip
        )
    
    def buscar_por_id(self, centro_custo_id: UUID) -> Dict[str, Any]:
        """
        Busca um centro de custo por ID
        
        Args:
            centro_custo_id: UUID do centro de custo
            
        Returns:
            Dados do centro de custo
        """
        return self.client.get(f"/costcenters/{centro_custo_id}")
    
    def criar(
        self,
        name: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Cria um novo centro de custo
        
        Args:
            name: Nome do centro de custo
            **kwargs: Outros campos opcionais
            
        Returns:
            Dados do centro de custo criado
        """
        payload = {"name": name}
        payload.update(kwargs)
        
        return self.client.post("/costcenters/FormatType=json", json_data=payload)
    
    def atualizar(
        self,
        centro_custo_id: UUID,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Atualiza um centro de custo existente
        
        Args:
            centro_custo_id: UUID do centro de custo
            **kwargs: Campos a atualizar
            
        Returns:
            Dados do centro de custo atualizado
        """
        return self.client.put(
            f"/costcenters/{centro_custo_id}",
            json_data=kwargs
        )
    
    def excluir(self, centro_custo_id: UUID) -> Dict[str, Any]:
        """
        Exclui um centro de custo
        
        Args:
            centro_custo_id: UUID do centro de custo
            
        Returns:
            Resposta da API
        """
        return self.client.delete(f"/costcenters/{centro_custo_id}")

