"""
Testes para interface de clientes do Nibo Obrigações
"""
import unittest
from uuid import UUID
from nibo_api.settings import NiboSettings
from nibo_api.obrigacoes.client import NiboObrigacoesClient


class TestClientes(unittest.TestCase):
    """Testes para a interface de clientes"""
    
    def setUp(self):
        """Configuração inicial dos testes"""
        self.config = NiboSettings()
        self.client = NiboObrigacoesClient(self.config)
    
    def test_listar_clientes(self):
        """Testa listagem de clientes"""
        # Primeiro obtém um ID de escritório
        escritorios = self.client.escritorios.listar()
        self.assertGreater(len(escritorios["items"]), 0, "Nenhum escritório encontrado")
        
        accounting_firm_id = UUID(escritorios["items"][0]["id"])
        resultado = self.client.clientes.listar(accounting_firm_id)
        
        self.assertIn("items", resultado)
        self.assertIsInstance(resultado["items"], list)
        # A API de Obrigações retorna 'metadata' ao invés de 'count'
        self.assertIn("metadata", resultado)
    
    def test_criar_cliente(self):
        """Testa criação de cliente"""
        # Primeiro obtém um ID de escritório
        escritorios = self.client.escritorios.listar()
        self.assertGreater(len(escritorios["items"]), 0, "Nenhum escritório encontrado")
        
        accounting_firm_id = UUID(escritorios["items"][0]["id"])
        import time
        # Usa timestamp para garantir código único
        code = f"TESTE-{int(time.time())}"
        resultado = self.client.clientes.criar(
            accounting_firm_id=accounting_firm_id,
            name="TESTE CLIENTE OBRIGACOES API",
            code=code,  # Campo obrigatório
            documentNumber="12345678909"  # CPF válido para teste
        )
        
        self.assertIn("id", resultado)
        self.assertEqual(resultado["name"], "TESTE CLIENTE OBRIGACOES API")


if __name__ == "__main__":
    unittest.main()

