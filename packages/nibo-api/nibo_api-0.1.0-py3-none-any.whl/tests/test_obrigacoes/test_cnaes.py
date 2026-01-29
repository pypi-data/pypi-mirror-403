"""
Testes para interface de CNAEs do Nibo Obrigações
"""
import unittest
from uuid import UUID
from nibo_api.settings import NiboSettings
from nibo_api.obrigacoes.client import NiboObrigacoesClient


class TestCNAEs(unittest.TestCase):
    """Testes para a interface de CNAEs"""
    
    def setUp(self):
        """Configuração inicial dos testes"""
        self.config = NiboSettings()
        self.client = NiboObrigacoesClient(self.config)
        # Obtém um ID de escritório para usar nos testes
        escritorios = self.client.escritorios.listar()
        self.assertGreater(len(escritorios["items"]), 0, "Nenhum escritório encontrado")
        self.accounting_firm_id = UUID(escritorios["items"][0]["id"])
    
    def test_listar_cnaes(self):
        """Testa listagem de CNAEs"""
        resultado = self.client.cnaes.listar(self.accounting_firm_id)
        
        # CNAEs retorna uma lista direta, não um objeto com items
        self.assertIsInstance(resultado, list)
        if len(resultado) > 0:
            self.assertIn("id", resultado[0])
            self.assertIn("description", resultado[0])
        else:
            self.fail("Nenhum CNAE encontrado")


if __name__ == "__main__":
    unittest.main()

