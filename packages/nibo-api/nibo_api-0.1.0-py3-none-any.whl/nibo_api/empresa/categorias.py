"""
Interface para gerenciamento de categorias no Nibo Empresa
"""
from typing import Optional, Dict, Any
from uuid import UUID

from nibo_api.common.client import BaseClient


class CategoriasInterface:
    """Interface para operações com categorias"""
    
    def __init__(self, client: BaseClient):
        """
        Inicializa a interface de categorias
        
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
        Lista todas as categorias
        
        Args:
            odata_filter: Filtro OData (ex: "type eq 'in'")
            odata_orderby: Campo para ordenação
            odata_top: Limite de registros
            odata_skip: Registros a pular
            
        Returns:
            Dicionário com 'items' (lista de categorias) e 'count' (total)
        """
        return self.client.get(
            "/schedules/categories",
            odata_filter=odata_filter,
            odata_orderby=odata_orderby,
            odata_top=odata_top,
            odata_skip=odata_skip
        )
    
    def listar_grupos(self) -> Dict[str, Any]:
        """
        Lista grupos de categorias
        
        Returns:
            Lista de grupos de categorias
        """
        return self.client.get("/schedules/categories/groups")
    
    def buscar_por_id(self, categoria_id: UUID) -> Dict[str, Any]:
        """
        Busca uma categoria por ID
        
        Args:
            categoria_id: UUID da categoria
            
        Returns:
            Dados da categoria
        """
        return self.client.get(f"/schedules/categories/{categoria_id}")
    
    def hierarquia(self) -> Dict[str, Any]:
        """
        Retorna a hierarquia das categorias de agendamento
        
        Returns:
            Hierarquia de categorias
        """
        return self.client.get("/schedules/categories/hierarchy")
    
    def criar(
        self,
        name: str,
        type: str,
        parent_id: Optional[UUID] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Cria uma nova categoria
        
        Args:
            name: Nome da categoria
            type: Tipo da categoria ('in' para receita, 'out' para despesa)
            parent_id: UUID da categoria pai (opcional)
            **kwargs: Outros campos opcionais
            
        Returns:
            Dados da categoria criada
        """
        payload = {
            "name": name,
            "type": type
        }
        
        if parent_id:
            payload["parentId"] = str(parent_id)
        
        payload.update(kwargs)
        
        return self.client.post("/schedules/categories/FormatType=json", json_data=payload)
    
    def criar_json(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Cria uma categoria usando payload JSON completo
        
        Args:
            payload: Dicionário completo com dados da categoria
            
        Returns:
            Dados da categoria criada
        """
        return self.client.post("/schedules/categories/FormatType=json", json_data=payload)

