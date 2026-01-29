"""
Interface para cobranças no Nibo Empresa
"""
from typing import Optional, Dict, Any
from uuid import UUID

from nibo_api.common.client import BaseClient


class CobrancasInterface:
    """Interface para operações com cobranças"""
    
    def __init__(self, client: BaseClient):
        """
        Inicializa a interface de cobranças
        
        Args:
            client: Instância do cliente HTTP base
        """
        self.client = client
    
    def listar_perfis_cobranca(
        self,
        odata_filter: Optional[str] = None,
        odata_orderby: Optional[str] = None,
        odata_top: Optional[int] = None,
        odata_skip: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Lista perfis de cobrança
        
        Args:
            odata_filter: Filtro OData
            odata_orderby: Campo para ordenação
            odata_top: Limite de registros
            odata_skip: Registros a pular
            
        Returns:
            Dicionário com 'items' (lista de perfis) e 'count' (total)
        """
        return self.client.get(
            "/charges/profiles",
            odata_filter=odata_filter,
            odata_orderby=odata_orderby,
            odata_top=odata_top,
            odata_skip=odata_skip
        )
    
    def listar_cobrancas(
        self,
        odata_filter: Optional[str] = None,
        odata_orderby: Optional[str] = None,
        odata_top: Optional[int] = None,
        odata_skip: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Lista cobranças
        
        Args:
            odata_filter: Filtro OData
            odata_orderby: Campo para ordenação
            odata_top: Limite de registros
            odata_skip: Registros a pular
            
        Returns:
            Dicionário com 'items' (lista de cobranças) e 'count' (total)
        """
        return self.client.get(
            "/charges",
            odata_filter=odata_filter,
            odata_orderby=odata_orderby,
            odata_top=odata_top,
            odata_skip=odata_skip
        )
    
    def criar_cobranca(
        self,
        schedule_id: UUID,
        profile_id: UUID,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Cria uma nova cobrança
        
        Args:
            schedule_id: UUID do agendamento
            profile_id: UUID do perfil de cobrança
            **kwargs: Outros campos opcionais
            
        Returns:
            Dados da cobrança criada
        """
        payload = {
            "scheduleId": str(schedule_id),
            "profileId": str(profile_id)
        }
        payload.update(kwargs)
        
        return self.client.post("/charges/FormatType=json", json_data=payload)
    
    def cancelar_cobranca(self, cobranca_id: UUID) -> Dict[str, Any]:
        """
        Cancela uma cobrança
        
        Args:
            cobranca_id: UUID da cobrança
            
        Returns:
            Resposta da API
        """
        return self.client.post(f"/charges/{cobranca_id}/cancel")

