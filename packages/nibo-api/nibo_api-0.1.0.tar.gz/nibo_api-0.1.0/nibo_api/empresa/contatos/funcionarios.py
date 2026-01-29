"""
Interface para gerenciamento de funcionários no Nibo Empresa
"""
from typing import Optional, Dict, Any
from uuid import UUID

from nibo_api.common.client import BaseClient


class FuncionariosInterface:
    """Interface para operações com funcionários"""
    
    def __init__(self, client: BaseClient):
        """
        Inicializa a interface de funcionários
        
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
        Lista todos os funcionários
        
        Args:
            odata_filter: Filtro OData
            odata_orderby: Campo para ordenação
            odata_top: Limite de registros
            odata_skip: Registros a pular
            
        Returns:
            Dicionário com 'items' (lista de funcionários) e 'count' (total)
        """
        return self.client.get(
            "/employees",
            odata_filter=odata_filter,
            odata_orderby=odata_orderby,
            odata_top=odata_top,
            odata_skip=odata_skip
        )
    
    def buscar_agendamentos_por_funcionario(
        self,
        funcionario_id: UUID,
        odata_filter: Optional[str] = None,
        odata_orderby: Optional[str] = None,
        odata_top: Optional[int] = None,
        odata_skip: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Busca agendamentos de um funcionário específico
        
        Args:
            funcionario_id: UUID do funcionário
            odata_filter: Filtro OData
            odata_orderby: Campo para ordenação
            odata_top: Limite de registros
            odata_skip: Registros a pular
            
        Returns:
            Lista de agendamentos do funcionário
        """
        return self.client.get(
            f"/employees/{funcionario_id}/schedules",
            odata_filter=odata_filter,
            odata_orderby=odata_orderby,
            odata_top=odata_top,
            odata_skip=odata_skip
        )
    
    def buscar_por_id(self, funcionario_id: UUID) -> Dict[str, Any]:
        """
        Busca um funcionário por ID
        
        Args:
            funcionario_id: UUID do funcionário
            
        Returns:
            Dados do funcionário
        """
        return self.client.get(f"/employees/{funcionario_id}")
    
    def criar(
        self,
        name: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Cria um novo funcionário
        
        Args:
            name: Nome do funcionário
            **kwargs: Outros campos opcionais
            
        Returns:
            Dados do funcionário criado
        """
        payload = {"name": name}
        payload.update(kwargs)
        
        return self.client.post("/employees/FormatType=json", json_data=payload)
    
    def atualizar(
        self,
        funcionario_id: UUID,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Atualiza um funcionário existente
        
        Args:
            funcionario_id: UUID do funcionário
            **kwargs: Campos a atualizar
            
        Returns:
            Dados do funcionário atualizado
        """
        return self.client.put(
            f"/employees/{funcionario_id}",
            json_data=kwargs
        )
    
    def excluir(self, funcionario_id: UUID) -> Dict[str, Any]:
        """
        Exclui um funcionário
        
        Args:
            funcionario_id: UUID do funcionário
            
        Returns:
            Resposta da API
        """
        return self.client.delete(f"/employees/{funcionario_id}")

