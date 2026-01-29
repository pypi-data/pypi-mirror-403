"""
Testes para interface de tarefas do Nibo Obrigações
"""
import unittest
from uuid import UUID
from nibo_api.settings import NiboSettings
from nibo_api.obrigacoes.client import NiboObrigacoesClient


class TestTarefas(unittest.TestCase):
    """Testes para a interface de tarefas"""
    
    def setUp(self):
        """Configuração inicial dos testes"""
        self.config = NiboSettings()
        self.client = NiboObrigacoesClient(self.config)
        # Obtém um ID de escritório para usar nos testes
        escritorios = self.client.escritorios.listar()
        self.assertGreater(len(escritorios["items"]), 0, "Nenhum escritório encontrado")
        self.accounting_firm_id = UUID(escritorios["items"][0]["id"])
    
    def test_listar_tarefas(self):
        """Testa listagem de tarefas"""
        resultado = self.client.tarefas.listar(self.accounting_firm_id)
        
        self.assertIn("items", resultado)
        self.assertIsInstance(resultado["items"], list)
        self.assertIn("metadata", resultado)
    
    def test_criar_tarefa(self):
        """Testa criação de tarefa"""
        resultado = self.client.tarefas.criar(
            accounting_firm_id=self.accounting_firm_id,
            name="TESTE TAREFA API"
        )
        
        # Status 202 pode retornar string vazia ou objeto com id
        if isinstance(resultado, dict):
            self.assertIn("id", resultado)
            if "name" in resultado:
                self.assertEqual(resultado["name"], "TESTE TAREFA API")
        else:
            # Se for string vazia (202 Accepted), consideramos sucesso
            self.assertIsInstance(resultado, str)


if __name__ == "__main__":
    unittest.main()

