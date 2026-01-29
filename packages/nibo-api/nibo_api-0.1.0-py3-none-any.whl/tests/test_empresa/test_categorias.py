"""
Testes para interface de categorias do Nibo Empresa
"""
import unittest
from uuid import UUID
from nibo_api.settings import NiboSettings
from nibo_api.empresa.client import NiboEmpresaClient


class TestCategorias(unittest.TestCase):
    """Testes para a interface de categorias"""
    
    def setUp(self):
        """Configuração inicial dos testes"""
        self.config = NiboSettings()
        self.client = NiboEmpresaClient(self.config)
    
    def test_listar_categorias(self):
        """Testa listagem de categorias"""
        resultado = self.client.categorias.listar()
        
        self.assertIn("items", resultado)
        self.assertIn("count", resultado)
        self.assertIsInstance(resultado["items"], list)
        self.assertIsInstance(resultado["count"], int)
    
    def test_listar_categorias_com_filtro(self):
        """Testa listagem de categorias com filtro OData"""
        resultado = self.client.categorias.listar(
            odata_filter="type eq 'in'"
        )
        
        self.assertIn("items", resultado)
        self.assertIn("count", resultado)
        
        # Verifica se todas as categorias retornadas são do tipo 'in'
        for categoria in resultado["items"]:
            self.assertEqual(categoria["type"], "in")
    
    def test_buscar_categoria_por_id(self):
        """Testa busca de categoria por ID"""
        # Primeiro lista categorias para pegar um ID válido
        categorias = self.client.categorias.listar(odata_top=1)
        
        if categorias["items"]:
            categoria_id = UUID(categorias["items"][0]["id"])
            resultado = self.client.categorias.buscar_por_id(categoria_id)
            
            self.assertIn("id", resultado)
            self.assertEqual(str(resultado["id"]), str(categoria_id))
    
    def test_listar_grupos(self):
        """Testa listagem de grupos de categorias"""
        resultado = self.client.categorias.listar_grupos()
        
        self.assertIsInstance(resultado, (dict, list))
    
    def test_hierarquia(self):
        """Testa busca da hierarquia de categorias"""
        resultado = self.client.categorias.hierarquia()
        
        self.assertIsInstance(resultado, (dict, list))


if __name__ == "__main__":
    unittest.main()

