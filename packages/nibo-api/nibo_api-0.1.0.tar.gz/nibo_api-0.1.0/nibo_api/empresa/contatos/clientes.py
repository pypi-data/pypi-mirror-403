"""
Interface para gerenciamento de clientes no Nibo Empresa
"""
from typing import Optional, Dict, Any, List
from uuid import UUID

from nibo_api.common.client import BaseClient
from nibo_api.common.models import Cliente


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
        odata_filter: Optional[str] = None,
        odata_orderby: Optional[str] = None,
        odata_top: Optional[int] = None,
        odata_skip: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Lista todos os clientes
        
        Args:
            odata_filter: Filtro OData (ex: "document/number eq '11497110000127'")
            odata_orderby: Campo para ordenação
            odata_top: Limite de registros
            odata_skip: Registros a pular
            
        Returns:
            Dicionário com 'items' (lista de clientes) e 'count' (total)
        """
        return self.client.get(
            "/customers",
            odata_filter=odata_filter,
            odata_orderby=odata_orderby,
            odata_top=odata_top,
            odata_skip=odata_skip
        )
    
    def buscar_por_id(self, cliente_id: UUID) -> Dict[str, Any]:
        """
        Busca um cliente por ID
        
        Args:
            cliente_id: UUID do cliente
            
        Returns:
            Dados do cliente
        """
        return self.client.get(f"/customers/{cliente_id}")
    
    def buscar_agendamentos_por_cliente(
        self,
        cliente_id: UUID,
        odata_filter: Optional[str] = None,
        odata_orderby: Optional[str] = None,
        odata_top: Optional[int] = None,
        odata_skip: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Busca agendamentos de um cliente específico
        
        Args:
            cliente_id: UUID do cliente
            odata_filter: Filtro OData
            odata_orderby: Campo para ordenação
            odata_top: Limite de registros
            odata_skip: Registros a pular
            
        Returns:
            Lista de agendamentos do cliente
        """
        return self.client.get(
            f"/customers/{cliente_id}/schedules",
            odata_filter=odata_filter,
            odata_orderby=odata_orderby,
            odata_top=odata_top,
            odata_skip=odata_skip
        )
    
    def criar(
        self,
        name: str,
        document_type: Optional[str] = None,
        document_number: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Cria um novo cliente
        
        Args:
            name: Nome do cliente
            document_type: Tipo de documento ('cnpj' ou 'cpf')
            document_number: Número do documento
            **kwargs: Outros campos opcionais (communication, address, etc.)
            
        Returns:
            Dados do cliente criado
        """
        payload = {"name": name}
        
        if document_type and document_number:
            payload["document"] = {
                "type": document_type,
                "number": document_number
            }
        
        # Adiciona outros campos se fornecidos
        payload.update(kwargs)
        
        return self.client.post("/customers/FormatType=json", json_data=payload)
    
    def atualizar(
        self,
        cliente_id: UUID,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Atualiza um cliente existente
        
        Args:
            cliente_id: UUID do cliente
            **kwargs: Campos a atualizar
            
        Returns:
            Dados do cliente atualizado
        """
        return self.client.put(
            f"/customers/{cliente_id}",
            json_data=kwargs
        )
    
    def excluir(self, cliente_id: UUID) -> Dict[str, Any]:
        """
        Exclui um cliente
        
        Args:
            cliente_id: UUID do cliente
            
        Returns:
            Resposta da API
        """
        return self.client.delete(f"/customers/{cliente_id}")

