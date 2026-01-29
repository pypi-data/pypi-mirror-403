"""
Interface para responsabilidades no Nibo Obrigações
"""
from typing import Optional, Dict, Any
from uuid import UUID

from nibo_api.common.client import BaseClient


class ResponsabilidadesInterface:
    """Interface para operações com responsabilidades"""
    
    def __init__(self, client: BaseClient):
        """
        Inicializa a interface de responsabilidades
        
        Args:
            client: Instância do cliente HTTP base
        """
        self.client = client
    
    def listar_responsaveis_clientes(
        self,
        accounting_firm_id: UUID,
        odata_filter: Optional[str] = None,
        odata_orderby: Optional[str] = None,
        odata_top: Optional[int] = None,
        odata_skip: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Lista responsáveis pelos clientes de um escritório
        
        Args:
            accounting_firm_id: UUID do escritório contábil
            odata_filter: Filtro OData
            odata_orderby: Campo para ordenação
            odata_top: Limite de registros
            odata_skip: Registros a pular
            
        Returns:
            Dicionário com 'items' (lista de responsáveis) e 'metadata'
        """
        return self.client.get(
            f"/accountingfirms/{accounting_firm_id}/responsibilities",
            odata_filter=odata_filter,
            odata_orderby=odata_orderby,
            odata_top=odata_top,
            odata_skip=odata_skip
        )
    
    def transferir_responsavel(
        self,
        accounting_firm_id: UUID,
        cliente_id: UUID,
        user_id: UUID,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Transfere responsável pelo cliente
        
        Args:
            accounting_firm_id: UUID do escritório contábil
            cliente_id: UUID do cliente
            user_id: UUID do usuário responsável
            **kwargs: Outros campos opcionais
            
        Returns:
            Resposta da API
        """
        payload = {
            "userId": str(user_id)
        }
        payload.update(kwargs)
        
        return self.client.post(
            f"/accountingfirms/{accounting_firm_id}/customers/{cliente_id}/responsibilities/transfer",
            json_data=payload
        )

