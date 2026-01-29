"""
Testes para interface de clientes do Nibo Empresa
"""
import unittest
from uuid import UUID
from nibo_api.settings import NiboSettings
from nibo_api.empresa.client import NiboEmpresaClient


class TestClientes(unittest.TestCase):
    """Testes para a interface de clientes"""
    
    def setUp(self):
        """Configuração inicial dos testes"""
        self.config = NiboSettings()
        self.client = NiboEmpresaClient(self.config)
    
    def test_listar_clientes(self):
        """Testa listagem de clientes"""
        resultado = self.client.clientes.listar()
        
        self.assertIn("items", resultado)
        self.assertIn("count", resultado)
        self.assertIsInstance(resultado["items"], list)
        self.assertIsInstance(resultado["count"], int)
    
    def test_listar_clientes_com_filtro(self):
        """Testa listagem de clientes com filtro OData"""
        resultado = self.client.clientes.listar(
            odata_filter="document/number eq '11497110000127'"
        )
        
        self.assertIn("items", resultado)
        self.assertIn("count", resultado)
    
    def test_buscar_cliente_por_id(self):
        """Testa busca de cliente por ID"""
        # Primeiro lista clientes para pegar um ID válido
        clientes = self.client.clientes.listar(odata_top=1)
        
        if clientes["items"]:
            cliente_id = UUID(clientes["items"][0]["id"])
            resultado = self.client.clientes.buscar_por_id(cliente_id)
            
            self.assertIn("id", resultado)
            self.assertEqual(str(resultado["id"]), str(cliente_id))
    
    def test_criar_cliente(self):
        """Testa criação de cliente"""
        resultado = self.client.clientes.criar(
            name="TESTE CLIENTE API",
            document_type="cnpj",
            document_number="11497110000127"
        )
        
        self.assertIn("id", resultado)
        self.assertEqual(resultado["name"], "TESTE CLIENTE API")
    
    def test_buscar_agendamentos_por_cliente(self):
        """Testa busca de agendamentos por cliente"""
        # Primeiro lista clientes para pegar um ID válido
        clientes = self.client.clientes.listar(odata_top=1)
        
        if clientes["items"]:
            cliente_id = UUID(clientes["items"][0]["id"])
            resultado = self.client.clientes.buscar_agendamentos_por_cliente(cliente_id)
            
            self.assertIn("items", resultado)
            self.assertIn("count", resultado)


if __name__ == "__main__":
    unittest.main()

