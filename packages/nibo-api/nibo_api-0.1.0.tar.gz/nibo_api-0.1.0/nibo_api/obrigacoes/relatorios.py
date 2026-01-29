"""
Interface para relatórios no Nibo Obrigações
"""
from typing import Optional, Dict, Any
from uuid import UUID

from nibo_api.common.client import BaseClient


class RelatoriosInterface:
    """Interface para operações com relatórios"""
    
    def __init__(self, client: BaseClient):
        """
        Inicializa a interface de relatórios
        
        Args:
            client: Instância do cliente HTTP base
        """
        self.client = client
    
    def listar_relatorios(
        self,
        accounting_firm_id: UUID,
        odata_filter: Optional[str] = None,
        odata_orderby: Optional[str] = None,
        odata_top: Optional[int] = None,
        odata_skip: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Lista relatórios do Nibo Obrigações de um escritório
        
        Args:
            accounting_firm_id: UUID do escritório contábil
            odata_filter: Filtro OData
            odata_orderby: Campo para ordenação
            odata_top: Limite de registros
            odata_skip: Registros a pular
            
        Returns:
            Dicionário com 'items' (lista de relatórios) e 'metadata'
        """
        return self.client.get(
            f"/accountingfirms/{accounting_firm_id}/reports/obligations/complete",
            odata_filter=odata_filter,
            odata_orderby=odata_orderby,
            odata_top=odata_top,
            odata_skip=odata_skip
        )
    
    def listar_fields(
        self,
        accounting_firm_id: UUID,
        odata_filter: Optional[str] = None,
        odata_orderby: Optional[str] = None,
        odata_top: Optional[int] = None,
        odata_skip: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Lista arquivos/obrigações usando o endpoint /fields
        Permite filtrar por Customer/Id, Department/Id ou Obligation/Id usando formato 'in'
        
        Exemplos de filtro:
        - Customer/Id in (id1, id2, id3)
        - Department/Id in (id1, id2)
        - Obligation/Id in ('234687', '525873')
        
        Args:
            accounting_firm_id: UUID do escritório contábil
            odata_filter: Filtro OData (ex: "Customer/Id in (id1, id2)")
            odata_orderby: Campo para ordenação
            odata_top: Limite de registros
            odata_skip: Registros a pular
            
        Returns:
            Dicionário com 'items' (lista de arquivos/obrigações) e 'metadata'
        """
        return self.client.get(
            f"/accountingfirms/{accounting_firm_id}/fields",
            odata_filter=odata_filter,
            odata_orderby=odata_orderby,
            odata_top=odata_top,
            odata_skip=odata_skip
        )

