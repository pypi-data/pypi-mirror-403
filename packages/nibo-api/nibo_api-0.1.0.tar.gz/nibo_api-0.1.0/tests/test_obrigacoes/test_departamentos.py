"""
Testes para interface de departamentos do Nibo Obrigações
"""
import unittest
from uuid import UUID
from nibo_api.settings import NiboSettings
from nibo_api.obrigacoes.client import NiboObrigacoesClient


class TestDepartamentos(unittest.TestCase):
    """Testes para a interface de departamentos"""
    
    def setUp(self):
        """Configuração inicial dos testes"""
        self.config = NiboSettings()
        self.client = NiboObrigacoesClient(self.config)
        # Obtém um ID de escritório para usar nos testes
        escritorios = self.client.escritorios.listar()
        self.assertGreater(len(escritorios["items"]), 0, "Nenhum escritório encontrado")
        self.accounting_firm_id = UUID(escritorios["items"][0]["id"])
    
    def test_listar_departamentos(self):
        """Testa listagem de departamentos"""
        resultado = self.client.departamentos.listar(self.accounting_firm_id)
        
        self.assertIn("items", resultado)
        self.assertIsInstance(resultado["items"], list)
        self.assertIn("metadata", resultado)


if __name__ == "__main__":
    unittest.main()

