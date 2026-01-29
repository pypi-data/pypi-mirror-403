"""
Testes para interface de usuários do Nibo Obrigações
"""
import unittest
from uuid import UUID
from nibo_api.settings import NiboSettings
from nibo_api.obrigacoes.client import NiboObrigacoesClient


class TestUsuarios(unittest.TestCase):
    """Testes para a interface de usuários"""
    
    def setUp(self):
        """Configuração inicial dos testes"""
        self.config = NiboSettings()
        self.client = NiboObrigacoesClient(self.config)
        # Obtém um ID de escritório para usar nos testes
        escritorios = self.client.escritorios.listar()
        self.assertGreater(len(escritorios["items"]), 0, "Nenhum escritório encontrado")
        self.accounting_firm_id = UUID(escritorios["items"][0]["id"])
    
    def test_listar_membros_equipe(self):
        """Testa listagem de membros da equipe"""
        resultado = self.client.usuarios.listar_membros_equipe(self.accounting_firm_id)
        
        self.assertIn("items", resultado)
        self.assertIsInstance(resultado["items"], list)
        self.assertIn("metadata", resultado)


if __name__ == "__main__":
    unittest.main()

