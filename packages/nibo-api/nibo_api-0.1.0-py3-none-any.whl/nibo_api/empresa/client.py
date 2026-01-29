"""
Cliente principal para a API Nibo Empresa
"""
from typing import Optional
from nibo_api.settings import NiboSettings
from nibo_api.common.client import BaseClient
from nibo_api.empresa.contatos.clientes import ClientesInterface
from nibo_api.empresa.contatos.fornecedores import FornecedoresInterface
from nibo_api.empresa.contatos.funcionarios import FuncionariosInterface
from nibo_api.empresa.contatos.socios import SociosInterface
from nibo_api.empresa.categorias import CategoriasInterface
from nibo_api.empresa.centro_custo import CentroCustoInterface
from nibo_api.empresa.organizacoes import OrganizacoesInterface
from nibo_api.empresa.agendamentos.receber import AgendamentosReceberInterface
from nibo_api.empresa.agendamentos.pagar import AgendamentosPagarInterface
from nibo_api.empresa.agendamentos.recebimentos import RecebimentosInterface
from nibo_api.empresa.agendamentos.pagamentos import PagamentosInterface
from nibo_api.empresa.agendamentos.arquivos import ArquivosAgendamentoInterface
from nibo_api.empresa.agendamentos.anotacoes import AnotacoesAgendamentoInterface
from nibo_api.empresa.conciliacao import ConciliacaoInterface
from nibo_api.empresa.contas_extratos import ContasExtratosInterface
from nibo_api.empresa.parcelamentos import ParcelamentosInterface
from nibo_api.empresa.arquivos import ArquivosInterface
from nibo_api.empresa.nota_fiscal import NotaFiscalInterface
from nibo_api.empresa.relatorios import RelatoriosInterface
from nibo_api.empresa.cobrancas import CobrancasInterface


class NiboEmpresaClient(BaseClient):
    """Cliente principal para interagir com a API Nibo Empresa"""
    
    def __init__(
        self, 
        config: Optional[NiboSettings] = None,
        organizacao_id: Optional[str] = None,
        organizacao_codigo: Optional[str] = None
    ):
        """
        Inicializa o cliente Nibo Empresa
        
        Args:
            config: Instância de NiboSettings. Se None, cria uma nova.
            organizacao_id: ID da organização (ex: "org_123")
            organizacao_codigo: Código simplificado da organização (ex: "empresa_principal")
            
        Raises:
            ValueError: Se nenhum identificador de organização for fornecido
        """
        if not organizacao_id and not organizacao_codigo:
            raise ValueError(
                "É necessário fornecer organizacao_id ou organizacao_codigo. "
                "Exemplo: NiboEmpresaClient(config, organizacao_id='org_123') ou "
                "NiboEmpresaClient(config, organizacao_codigo='empresa_principal')"
            )
        
        if config is None:
            config = NiboSettings()
        super().__init__(
            config, 
            base_url=config.empresa_base_url,
            organizacao_id=organizacao_id,
            organizacao_codigo=organizacao_codigo
        )
        
        # Inicializa interfaces
        self.clientes = ClientesInterface(self)
        self.fornecedores = FornecedoresInterface(self)
        self.funcionarios = FuncionariosInterface(self)
        self.socios = SociosInterface(self)
        self.categorias = CategoriasInterface(self)
        self.centro_custo = CentroCustoInterface(self)
        self.organizacoes = OrganizacoesInterface(self)
        self.agendamentos_receber = AgendamentosReceberInterface(self)
        self.agendamentos_pagar = AgendamentosPagarInterface(self)
        self.recebimentos = RecebimentosInterface(self)
        self.pagamentos = PagamentosInterface(self)
        self.agendamentos_arquivos = ArquivosAgendamentoInterface(self)
        self.agendamentos_anotacoes = AnotacoesAgendamentoInterface(self)
        self.conciliacao = ConciliacaoInterface(self)
        self.contas_extratos = ContasExtratosInterface(self)
        self.parcelamentos = ParcelamentosInterface(self)
        self.arquivos = ArquivosInterface(self)
        self.nota_fiscal = NotaFiscalInterface(self)
        self.relatorios = RelatoriosInterface(self)
        self.cobrancas = CobrancasInterface(self)

