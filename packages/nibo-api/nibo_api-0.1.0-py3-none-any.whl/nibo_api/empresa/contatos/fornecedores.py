"""
Interface para gerenciamento de fornecedores no Nibo Empresa
"""
from typing import Optional, Dict, Any
from uuid import UUID

from nibo_api.common.client import BaseClient


class FornecedoresInterface:
    """Interface para operações com fornecedores"""
    
    def __init__(self, client: BaseClient):
        """
        Inicializa a interface de fornecedores
        
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
        Lista todos os fornecedores
        
        Args:
            odata_filter: Filtro OData
            odata_orderby: Campo para ordenação
            odata_top: Limite de registros
            odata_skip: Registros a pular
            
        Returns:
            Dicionário com 'items' (lista de fornecedores) e 'count' (total)
        """
        return self.client.get(
            "/suppliers",
            odata_filter=odata_filter,
            odata_orderby=odata_orderby,
            odata_top=odata_top,
            odata_skip=odata_skip
        )
    
    def buscar_agendamentos_por_fornecedor(
        self,
        fornecedor_id: UUID,
        odata_filter: Optional[str] = None,
        odata_orderby: Optional[str] = None,
        odata_top: Optional[int] = None,
        odata_skip: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Busca agendamentos de um fornecedor específico
        
        Args:
            fornecedor_id: UUID do fornecedor
            odata_filter: Filtro OData
            odata_orderby: Campo para ordenação
            odata_top: Limite de registros
            odata_skip: Registros a pular
            
        Returns:
            Lista de agendamentos do fornecedor
        """
        return self.client.get(
            f"/suppliers/{fornecedor_id}/schedules",
            odata_filter=odata_filter,
            odata_orderby=odata_orderby,
            odata_top=odata_top,
            odata_skip=odata_skip
        )
    
    def buscar_por_id(self, fornecedor_id: UUID) -> Dict[str, Any]:
        """
        Busca um fornecedor por ID
        
        Args:
            fornecedor_id: UUID do fornecedor
            
        Returns:
            Dados do fornecedor
        """
        return self.client.get(f"/suppliers/{fornecedor_id}")
    
    def criar(
        self,
        name: str,
        document_type: Optional[str] = None,
        document_number: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Cria um novo fornecedor
        
        Args:
            name: Nome do fornecedor
            document_type: Tipo de documento ('cnpj' ou 'cpf')
            document_number: Número do documento
            **kwargs: Outros campos opcionais
            
        Returns:
            Dados do fornecedor criado
        """
        payload = {"name": name}
        
        if document_type and document_number:
            payload["document"] = {
                "type": document_type,
                "number": document_number
            }
        
        payload.update(kwargs)
        
        return self.client.post("/suppliers/FormatType=json", json_data=payload)
    
    def criar_json(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Cria um fornecedor usando payload JSON completo
        
        Args:
            payload: Dicionário completo com dados do fornecedor
            
        Returns:
            Dados do fornecedor criado
        """
        return self.client.post("/suppliers/FormatType=json", json_data=payload)
    
    def atualizar(
        self,
        fornecedor_id: UUID,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Atualiza um fornecedor existente
        
        Args:
            fornecedor_id: UUID do fornecedor
            **kwargs: Campos a atualizar
            
        Returns:
            Dados do fornecedor atualizado
        """
        return self.client.put(
            f"/suppliers/{fornecedor_id}",
            json_data=kwargs
        )
    
    def excluir(self, fornecedor_id: UUID) -> Dict[str, Any]:
        """
        Exclui um fornecedor
        
        Args:
            fornecedor_id: UUID do fornecedor
            
        Returns:
            Resposta da API
        """
        return self.client.delete(f"/suppliers/{fornecedor_id}")

