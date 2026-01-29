"""
Interface para pagamentos (contas pagas) no Nibo Empresa
"""
from typing import Optional, Dict, Any
from uuid import UUID

from nibo_api.common.client import BaseClient


class PagamentosInterface:
    """Interface para operações com pagamentos (contas pagas)"""
    
    def __init__(self, client: BaseClient):
        """
        Inicializa a interface de pagamentos
        
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
        Lista pagamentos (contas pagas)
        
        Args:
            odata_filter: Filtro OData
            odata_orderby: Campo para ordenação
            odata_top: Limite de registros
            odata_skip: Registros a pular
            
        Returns:
            Dicionário com 'items' (lista de pagamentos) e 'count' (total)
        """
        return self.client.get(
            "/entries/debit",
            odata_filter=odata_filter,
            odata_orderby=odata_orderby,
            odata_top=odata_top,
            odata_skip=odata_skip
        )
    
    def criar(
        self,
        categories: list,
        stakeholder_id: UUID,
        payment_date: str,
        description: str,
        reference: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Cria um novo pagamento
        
        Args:
            categories: Lista de categorias com categoryId, value e description
            stakeholder_id: UUID do stakeholder (fornecedor)
            payment_date: Data do pagamento (formato: DD/MM/YYYY)
            description: Descrição do pagamento
            reference: Referência do pagamento (opcional)
            **kwargs: Outros campos opcionais
            
        Returns:
            Dados do pagamento criado
        """
        payload = {
            "categories": categories,
            "stakeholderId": str(stakeholder_id),
            "paymentDate": payment_date,
            "description": description
        }
        
        if reference:
            payload["reference"] = reference
        
        payload.update(kwargs)
        
        return self.client.post("/entries/debit", json_data=payload)
    
    def criar_json(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Cria um pagamento usando payload JSON completo
        
        Args:
            payload: Dicionário completo com dados do pagamento
            
        Returns:
            Dados do pagamento criado
        """
        return self.client.post("/entries/debit", json_data=payload)
    
    def excluir(self, entry_id: UUID) -> Dict[str, Any]:
        """
        Exclui um pagamento
        
        Args:
            entry_id: UUID do pagamento
            
        Returns:
            Resposta da API
        """
        return self.client.delete(f"/entries/debit/{entry_id}")

