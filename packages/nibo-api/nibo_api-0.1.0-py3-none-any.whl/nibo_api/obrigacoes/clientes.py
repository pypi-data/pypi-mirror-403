"""
Interface para clientes no Nibo Obrigações
"""
from typing import Optional, Dict, Any
from uuid import UUID

from nibo_api.common.client import BaseClient


class ClientesInterface:
    """Interface para operações com clientes"""
    
    def __init__(self, client: BaseClient):
        """
        Inicializa a interface de clientes
        
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
        Lista todos os clientes de um escritório
        
        Args:
            accounting_firm_id: UUID do escritório contábil
            odata_filter: Filtro OData
            odata_orderby: Campo para ordenação
            odata_top: Limite de registros
            odata_skip: Registros a pular
            
        Returns:
            Dicionário com 'items' (lista de clientes) e 'metadata'
        """
        return self.client.get(
            f"/accountingfirms/{accounting_firm_id}/customers",
            odata_filter=odata_filter,
            odata_orderby=odata_orderby,
            odata_top=odata_top,
            odata_skip=odata_skip
        )
    
    def criar(
        self,
        accounting_firm_id: UUID,
        name: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Cria um novo cliente em um escritório
        
        Args:
            accounting_firm_id: UUID do escritório contábil
            name: Nome do cliente
            **kwargs: Outros campos opcionais
            
        Returns:
            Dados do cliente criado
        """
        payload = {
            "name": name
        }
        payload.update(kwargs)
        
        return self.client.post(
            f"/accountingfirms/{accounting_firm_id}/customers",
            json_data=payload
        )
    
    def adicionar_grupo_clientes(
        self,
        accounting_firm_id: UUID,
        cliente_id: UUID,
        group_id: UUID,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Adiciona cliente ao grupo de clientes
        
        Args:
            accounting_firm_id: UUID do escritório contábil
            cliente_id: UUID do cliente
            group_id: UUID do grupo
            **kwargs: Outros campos opcionais
            
        Returns:
            Resposta da API
        """
        payload = {
            "groupId": str(group_id)
        }
        payload.update(kwargs)
        
        return self.client.post(
            f"/accountingfirms/{accounting_firm_id}/customers/{cliente_id}/groups",
            json_data=payload
        )
    
    def atualizar(
        self,
        accounting_firm_id: UUID,
        cliente_id: UUID,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Atualiza um cliente existente
        
        Args:
            accounting_firm_id: UUID do escritório contábil
            cliente_id: UUID do cliente
            **kwargs: Campos a atualizar
            
        Returns:
            Dados do cliente atualizado
        """
        return self.client.put(
            f"/accountingfirms/{accounting_firm_id}/customers/{cliente_id}",
            json_data=kwargs
        )

