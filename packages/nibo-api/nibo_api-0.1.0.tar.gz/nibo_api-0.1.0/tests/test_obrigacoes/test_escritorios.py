"""
Testes para interface de escritórios do Nibo Obrigações
"""
import unittest
from nibo_api.settings import NiboSettings
from nibo_api.obrigacoes.client import NiboObrigacoesClient


class TestEscritorios(unittest.TestCase):
    """Testes para a interface de escritórios"""
    
    def setUp(self):
        """Configuração inicial dos testes"""
        self.config = NiboSettings()
        self.client = NiboObrigacoesClient(self.config)
    
    def test_listar_escritorios(self):
        """Testa listagem de escritórios"""
        resultado = self.client.escritorios.listar()
        
        self.assertIn("items", resultado)
        self.assertIsInstance(resultado["items"], list)
        # A API de Obrigações retorna 'metadata' (pode ser None) ao invés de 'count'
        self.assertIn("metadata", resultado)


if __name__ == "__main__":
    unittest.main()

