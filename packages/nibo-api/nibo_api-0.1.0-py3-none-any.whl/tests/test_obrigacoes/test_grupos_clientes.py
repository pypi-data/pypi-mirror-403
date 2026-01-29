"""
Testes para interface de grupos de clientes do Nibo Obrigações
"""
import unittest
from uuid import UUID
from nibo_api.settings import NiboSettings
from nibo_api.obrigacoes.client import NiboObrigacoesClient


class TestGruposClientes(unittest.TestCase):
    """Testes para a interface de grupos de clientes"""
    
    def setUp(self):
        """Configuração inicial dos testes"""
        self.config = NiboSettings()
        self.client = NiboObrigacoesClient(self.config)
        # Obtém um ID de escritório para usar nos testes
        escritorios = self.client.escritorios.listar()
        self.assertGreater(len(escritorios["items"]), 0, "Nenhum escritório encontrado")
        self.accounting_firm_id = UUID(escritorios["items"][0]["id"])
    
    def test_listar_grupos_clientes(self):
        """Testa listagem de grupos de clientes"""
        resultado = self.client.grupos_clientes.listar(self.accounting_firm_id)
        
        self.assertIn("items", resultado)
        self.assertIsInstance(resultado["items"], list)
        self.assertIn("metadata", resultado)


if __name__ == "__main__":
    unittest.main()

