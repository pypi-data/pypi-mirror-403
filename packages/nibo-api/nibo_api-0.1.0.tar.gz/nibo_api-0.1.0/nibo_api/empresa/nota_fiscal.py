"""
Interface para nota fiscal no Nibo Empresa
"""
from typing import Optional, Dict, Any
from uuid import UUID

from nibo_api.common.client import BaseClient


class NotaFiscalInterface:
    """Interface para operações com nota fiscal"""
    
    def __init__(self, client: BaseClient):
        """
        Inicializa a interface de nota fiscal
        
        Args:
            client: Instância do cliente HTTP base
        """
        self.client = client
    
    def listar_perfis_servico(
        self,
        odata_filter: Optional[str] = None,
        odata_orderby: Optional[str] = None,
        odata_top: Optional[int] = None,
        odata_skip: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Lista perfis de serviço
        
        Args:
            odata_filter: Filtro OData
            odata_orderby: Campo para ordenação
            odata_top: Limite de registros
            odata_skip: Registros a pular
            
        Returns:
            Dicionário com 'items' (lista de perfis) e 'count' (total)
        """
        return self.client.get(
            "/nfse/profiles",
            odata_filter=odata_filter,
            odata_orderby=odata_orderby,
            odata_top=odata_top,
            odata_skip=odata_skip
        )
    
    def listar_nfs(
        self,
        odata_filter: Optional[str] = None,
        odata_orderby: Optional[str] = None,
        odata_top: Optional[int] = None,
        odata_skip: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Lista NFS-e
        
        Args:
            odata_filter: Filtro OData
            odata_orderby: Campo para ordenação
            odata_top: Limite de registros
            odata_skip: Registros a pular
            
        Returns:
            Dicionário com 'items' (lista de NFS-e) e 'count' (total)
        """
        return self.client.get(
            "/nfse",
            odata_filter=odata_filter,
            odata_orderby=odata_orderby,
            odata_top=odata_top,
            odata_skip=odata_skip
        )
    
    def emitir_nfse(
        self,
        schedule_id: UUID,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Emite uma NFS-e
        
        Args:
            schedule_id: UUID do agendamento
            **kwargs: Outros campos opcionais
            
        Returns:
            Dados da NFS-e emitida
        """
        payload = {
            "scheduleId": str(schedule_id)
        }
        payload.update(kwargs)
        
        return self.client.post("/nfse/emit", json_data=payload)
    
    def cancelar_nfse(
        self,
        nfse_id: UUID,
        reason: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Cancela uma NFS-e
        
        Args:
            nfse_id: UUID da NFS-e
            reason: Motivo do cancelamento
            **kwargs: Outros campos opcionais
            
        Returns:
            Resposta da API
        """
        payload = {
            "reason": reason
        }
        payload.update(kwargs)
        
        return self.client.post(f"/nfse/{nfse_id}/cancel", json_data=payload)

