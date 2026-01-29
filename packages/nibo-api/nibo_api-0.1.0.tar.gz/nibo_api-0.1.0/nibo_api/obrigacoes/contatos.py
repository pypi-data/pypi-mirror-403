"""
Interface para contatos no Nibo Obrigações
"""
from typing import Optional, Dict, Any
from uuid import UUID

from nibo_api.common.client import BaseClient


class ContatosInterface:
    """Interface para operações com contatos"""
    
    def __init__(self, client: BaseClient):
        """
        Inicializa a interface de contatos
        
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
        Lista todos os contatos de um escritório
        
        Args:
            accounting_firm_id: UUID do escritório contábil
            odata_filter: Filtro OData
            odata_orderby: Campo para ordenação
            odata_top: Limite de registros
            odata_skip: Registros a pular
            
        Returns:
            Dicionário com 'items' (lista de contatos) e 'metadata'
        """
        return self.client.get(
            f"/accountingfirms/{accounting_firm_id}/contacts",
            odata_filter=odata_filter,
            odata_orderby=odata_orderby,
            odata_top=odata_top,
            odata_skip=odata_skip
        )
    
    def buscar_por_id(
        self,
        accounting_firm_id: UUID,
        contato_id: UUID
    ) -> Dict[str, Any]:
        """
        Busca um contato específico
        
        Args:
            accounting_firm_id: UUID do escritório contábil
            contato_id: UUID do contato
            
        Returns:
            Dados do contato
        """
        return self.client.get(
            f"/accountingfirms/{accounting_firm_id}/contacts/{contato_id}"
        )
    
    def listar_departamentos(
        self,
        accounting_firm_id: UUID,
        contato_id: UUID,
        odata_filter: Optional[str] = None,
        odata_orderby: Optional[str] = None,
        odata_top: Optional[int] = None,
        odata_skip: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Lista os departamentos de um contato
        
        Args:
            accounting_firm_id: UUID do escritório contábil
            contato_id: UUID do contato
            odata_filter: Filtro OData
            odata_orderby: Campo para ordenação
            odata_top: Limite de registros
            odata_skip: Registros a pular
            
        Returns:
            Dicionário com 'items' (lista de departamentos) e 'metadata'
        """
        return self.client.get(
            f"/accountingfirms/{accounting_firm_id}/contacts/{contato_id}/departments",
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
        Cria um novo contato
        
        Args:
            accounting_firm_id: UUID do escritório contábil
            name: Nome do contato
            **kwargs: Outros campos opcionais
            
        Returns:
            Dados do contato criado
        """
        payload = {
            "name": name
        }
        payload.update(kwargs)
        
        return self.client.post(
            f"/accountingfirms/{accounting_firm_id}/contacts",
            json_data=payload
        )
    
    def adicionar_departamentos(
        self,
        accounting_firm_id: UUID,
        contato_id: UUID,
        department_ids: list,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Adiciona departamentos a um contato
        
        Args:
            accounting_firm_id: UUID do escritório contábil
            contato_id: UUID do contato
            department_ids: Lista de UUIDs dos departamentos
            **kwargs: Outros campos opcionais
            
        Returns:
            Resposta da API
        """
        payload = {
            "departmentIds": [str(dep_id) for dep_id in department_ids]
        }
        payload.update(kwargs)
        
        return self.client.post(
            f"/accountingfirms/{accounting_firm_id}/contacts/{contato_id}/departments",
            json_data=payload
        )
    
    def remover_departamento(
        self,
        accounting_firm_id: UUID,
        contato_id: UUID,
        department_id: UUID
    ) -> Dict[str, Any]:
        """
        Remove departamento de um contato
        
        Args:
            accounting_firm_id: UUID do escritório contábil
            contato_id: UUID do contato
            department_id: UUID do departamento
            
        Returns:
            Resposta da API
        """
        return self.client.delete(
            f"/accountingfirms/{accounting_firm_id}/contacts/{contato_id}/departments/{department_id}"
        )

