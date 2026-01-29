"""
Testes para interface de agendamentos de recebimento do Nibo Empresa
"""
import unittest
from uuid import UUID
from nibo_api.settings import NiboSettings
from nibo_api.empresa.client import NiboEmpresaClient


class TestAgendamentosReceber(unittest.TestCase):
    """Testes para a interface de agendamentos de recebimento"""
    
    def setUp(self):
        """Configuração inicial dos testes"""
        self.config = NiboSettings()
        self.client = NiboEmpresaClient(self.config)
    
    def test_listar_abertos(self):
        """Testa listagem de recebimentos agendados em aberto"""
        resultado = self.client.agendamentos_receber.listar_abertos()
        
        self.assertIn("items", resultado)
        self.assertIn("count", resultado)
        self.assertIsInstance(resultado["items"], list)
        self.assertIsInstance(resultado["count"], int)
    
    def test_listar_abertos_com_filtro(self):
        """Testa listagem de recebimentos agendados com filtro OData"""
        resultado = self.client.agendamentos_receber.listar_abertos(
            odata_filter="stakeholder/cpfCnpj eq '11497110000127'"
        )
        
        self.assertIn("items", resultado)
        self.assertIn("count", resultado)
    
    def test_listar_vencidos(self):
        """Testa listagem de recebimentos agendados vencidos"""
        resultado = self.client.agendamentos_receber.listar_vencidos()
        
        self.assertIn("items", resultado)
        self.assertIn("count", resultado)
    
    def test_listar_todos(self):
        """Testa listagem de todos os recebimentos agendados"""
        resultado = self.client.agendamentos_receber.listar_todos()
        
        self.assertIn("items", resultado)
        self.assertIn("count", resultado)
    
    def test_buscar_por_agendamento(self):
        """Testa busca de recebimento por ID do agendamento"""
        # Primeiro lista agendamentos para pegar um ID válido
        agendamentos = self.client.agendamentos_receber.listar_abertos(odata_top=1)
        
        if agendamentos["items"]:
            schedule_id = UUID(agendamentos["items"][0]["scheduleId"])
            resultado = self.client.agendamentos_receber.buscar_por_agendamento(schedule_id)
            
            self.assertIn("scheduleId", resultado)
            self.assertEqual(str(resultado["scheduleId"]), str(schedule_id))
    
    def test_agendar_recebimento(self):
        """Testa agendamento de recebimento"""
        # Primeiro busca uma categoria e um cliente válidos
        categorias = self.client.categorias.listar(odata_filter="type eq 'in'", odata_top=1)
        clientes = self.client.clientes.listar(odata_top=1)
        
        if categorias["items"] and clientes["items"]:
            categoria_id = categorias["items"][0]["id"]
            cliente_id = UUID(clientes["items"][0]["id"])
            
            resultado = self.client.agendamentos_receber.agendar(
                categories=[{
                    "categoryId": categoria_id,
                    "value": "100.00",
                    "description": "TESTE API"
                }],
                stakeholder_id=cliente_id,
                schedule_date="31/12/2024",
                due_date="31/12/2024",
                description="Teste de agendamento via API",
                reference="TEST-API"
            )
            
            self.assertIn("scheduleId", resultado)


if __name__ == "__main__":
    unittest.main()

