"""
Testes para interface de contatos do Nibo Obrigações
"""
import unittest
from uuid import UUID
from nibo_api.settings import NiboSettings
from nibo_api.obrigacoes.client import NiboObrigacoesClient


class TestContatos(unittest.TestCase):
    """Testes para a interface de contatos"""
    
    def setUp(self):
        """Configuração inicial dos testes"""
        self.config = NiboSettings()
        self.client = NiboObrigacoesClient(self.config)
    
    def test_listar_contatos(self):
        """Testa listagem de contatos"""
        # Primeiro obtém um ID de escritório
        escritorios = self.client.escritorios.listar()
        self.assertGreater(len(escritorios["items"]), 0, "Nenhum escritório encontrado")
        
        accounting_firm_id = UUID(escritorios["items"][0]["id"])
        resultado = self.client.contatos.listar(accounting_firm_id)
        
        self.assertIn("items", resultado)
        self.assertIsInstance(resultado["items"], list)
        self.assertIn("metadata", resultado)
    
    def test_buscar_contato_por_id(self):
        """Testa busca de contato por ID"""
        # Primeiro obtém um ID de escritório e lista contatos
        escritorios = self.client.escritorios.listar()
        self.assertGreater(len(escritorios["items"]), 0, "Nenhum escritório encontrado")
        
        accounting_firm_id = UUID(escritorios["items"][0]["id"])
        contatos = self.client.contatos.listar(accounting_firm_id, odata_top=1)
        
        if contatos["items"]:
            contato_id = UUID(contatos["items"][0]["id"])
            resultado = self.client.contatos.buscar_por_id(accounting_firm_id, contato_id)
            
            self.assertIn("id", resultado)
            self.assertEqual(str(resultado["id"]), str(contato_id))
    
    def test_listar_departamentos(self):
        """Testa listagem de departamentos de um contato"""
        # Primeiro obtém um ID de escritório e lista contatos
        escritorios = self.client.escritorios.listar()
        self.assertGreater(len(escritorios["items"]), 0, "Nenhum escritório encontrado")
        
        accounting_firm_id = UUID(escritorios["items"][0]["id"])
        contatos = self.client.contatos.listar(accounting_firm_id, odata_top=1)
        
        if contatos["items"]:
            contato_id = UUID(contatos["items"][0]["id"])
            resultado = self.client.contatos.listar_departamentos(accounting_firm_id, contato_id)
            
            self.assertIsInstance(resultado, (dict, list))


if __name__ == "__main__":
    unittest.main()

