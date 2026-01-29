"""
Interface para contas e extratos no Nibo Empresa
"""
from typing import Optional, Dict, Any
from uuid import UUID

from nibo_api.common.client import BaseClient


class ContasExtratosInterface:
    """Interface para operações com contas e extratos"""
    
    def __init__(self, client: BaseClient):
        """
        Inicializa a interface de contas e extratos
        
        Args:
            client: Instância do cliente HTTP base
        """
        self.client = client
    
    def consultar_saldo(
        self,
        account_id: UUID,
        date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Consulta saldo de uma conta
        
        Args:
            account_id: UUID da conta
            date: Data para consulta (formato: YYYY-MM-DD)
            
        Returns:
            Saldo da conta
        """
        params = {}
        if date:
            params["date"] = date
        
        return self.client.get(f"/accounts/{account_id}/balance", params=params)
    
    def consultar_extrato(
        self,
        account_id: UUID,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        odata_filter: Optional[str] = None,
        odata_orderby: Optional[str] = None,
        odata_top: Optional[int] = None,
        odata_skip: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Consulta extrato de uma conta
        
        Args:
            account_id: UUID da conta
            start_date: Data inicial (formato: YYYY-MM-DD)
            end_date: Data final (formato: YYYY-MM-DD)
            odata_filter: Filtro OData
            odata_orderby: Campo para ordenação
            odata_top: Limite de registros
            odata_skip: Registros a pular
            
        Returns:
            Extrato da conta
        """
        params = {}
        if start_date:
            params["startDate"] = start_date
        if end_date:
            params["endDate"] = end_date
        
        return self.client.get(
            f"/accounts/{account_id}/statement",
            params=params,
            odata_filter=odata_filter,
            odata_orderby=odata_orderby,
            odata_top=odata_top,
            odata_skip=odata_skip
        )
    
    def listar_contas(
        self,
        odata_filter: Optional[str] = None,
        odata_orderby: Optional[str] = None,
        odata_top: Optional[int] = None,
        odata_skip: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Lista contas bancárias
        
        Args:
            odata_filter: Filtro OData
            odata_orderby: Campo para ordenação
            odata_top: Limite de registros
            odata_skip: Registros a pular
            
        Returns:
            Dicionário com 'items' (lista de contas) e 'count' (total)
        """
        return self.client.get(
            "/accounts",
            odata_filter=odata_filter,
            odata_orderby=odata_orderby,
            odata_top=odata_top,
            odata_skip=odata_skip
        )
    
    def criar_conta(
        self,
        name: str,
        bank_id: UUID,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Cria uma nova conta bancária
        
        Args:
            name: Nome da conta
            bank_id: UUID do banco
            **kwargs: Outros campos opcionais
            
        Returns:
            Dados da conta criada
        """
        payload = {
            "name": name,
            "bankId": str(bank_id)
        }
        payload.update(kwargs)
        
        return self.client.post("/accounts/FormatType=json", json_data=payload)
    
    def atualizar_conta(
        self,
        account_id: UUID,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Atualiza uma conta bancária
        
        Args:
            account_id: UUID da conta
            **kwargs: Campos a atualizar
            
        Returns:
            Dados da conta atualizada
        """
        return self.client.put(
            f"/accounts/{account_id}",
            json_data=kwargs
        )
    
    def listar_transferencias(
        self,
        odata_filter: Optional[str] = None,
        odata_orderby: Optional[str] = None,
        odata_top: Optional[int] = None,
        odata_skip: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Lista transferências
        
        Args:
            odata_filter: Filtro OData
            odata_orderby: Campo para ordenação
            odata_top: Limite de registros
            odata_skip: Registros a pular
            
        Returns:
            Dicionário com 'items' (lista de transferências) e 'count' (total)
        """
        return self.client.get(
            "/transfers",
            odata_filter=odata_filter,
            odata_orderby=odata_orderby,
            odata_top=odata_top,
            odata_skip=odata_skip
        )
    
    def criar_transferencia(
        self,
        from_account_id: UUID,
        to_account_id: UUID,
        value: float,
        date: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Cria uma nova transferência
        
        Args:
            from_account_id: UUID da conta de origem
            to_account_id: UUID da conta de destino
            value: Valor da transferência
            date: Data da transferência (formato: DD/MM/YYYY)
            **kwargs: Outros campos opcionais
            
        Returns:
            Dados da transferência criada
        """
        payload = {
            "fromAccountId": str(from_account_id),
            "toAccountId": str(to_account_id),
            "value": value,
            "date": date
        }
        payload.update(kwargs)
        
        return self.client.post("/transfers/FormatType=json", json_data=payload)
    
    def excluir_transferencia(self, transfer_id: UUID) -> Dict[str, Any]:
        """
        Exclui uma transferência
        
        Args:
            transfer_id: UUID da transferência
            
        Returns:
            Resposta da API
        """
        return self.client.delete(f"/transfers/{transfer_id}")
    
    def listar_bancos(
        self,
        odata_filter: Optional[str] = None,
        odata_orderby: Optional[str] = None,
        odata_top: Optional[int] = None,
        odata_skip: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Lista bancos
        
        Args:
            odata_filter: Filtro OData
            odata_orderby: Campo para ordenação
            odata_top: Limite de registros
            odata_skip: Registros a pular
            
        Returns:
            Dicionário com 'items' (lista de bancos) e 'count' (total)
        """
        return self.client.get(
            "/banks",
            odata_filter=odata_filter,
            odata_orderby=odata_orderby,
            odata_top=odata_top,
            odata_skip=odata_skip
        )
    
    def buscar_banco_por_id(self, bank_id: UUID) -> Dict[str, Any]:
        """
        Busca um banco por ID
        
        Args:
            bank_id: UUID do banco
            
        Returns:
            Dados do banco
        """
        return self.client.get(f"/banks/{bank_id}")

