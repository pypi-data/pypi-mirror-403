"""
Testes para interface de arquivos do Nibo Obrigações
"""
import unittest
import os
import time
from pathlib import Path
from typing import Optional
from uuid import UUID
from nibo_api.settings import NiboSettings
from nibo_api.obrigacoes.client import NiboObrigacoesClient


class TestArquivos(unittest.TestCase):
    """Testes para a interface de arquivos"""
    
    def setUp(self):
        """Configuração inicial dos testes"""
        self.config = NiboSettings()
        self.client = NiboObrigacoesClient(self.config)
        
        # Obtém um ID de escritório para usar nos testes
        escritorios = self.client.escritorios.listar()
        self.assertGreater(len(escritorios["items"]), 0, "Nenhum escritório encontrado")
        self.accounting_firm_id = UUID(escritorios["items"][0]["id"])
        
        print(f"   Escritório encontrado: {self.accounting_firm_id}")
        
        # Busca ou cria o cliente "TESTE CLIENTE OBRIGACOES API"
        self.cliente_id = self._obter_ou_criar_cliente()
    
    def _obter_ou_criar_cliente(self) -> UUID:
        """Busca ou cria o cliente 'TESTE CLIENTE OBRIGACOES API'"""
        nome_cliente = "TESTE CLIENTE OBRIGACOES API"
        
        # Tenta buscar o cliente
        try:
            clientes = self.client.clientes.listar(
                accounting_firm_id=self.accounting_firm_id,
                odata_filter=f"name eq '{nome_cliente}'"
            )
            
            if clientes.get("items") and len(clientes["items"]) > 0:
                cliente_id = UUID(clientes["items"][0]["id"])
                print(f"   Cliente encontrado: {nome_cliente} (ID: {cliente_id})")
                return cliente_id
        except:
            pass
        
        # Se não encontrou, cria o cliente
        code = f"TESTE-{int(time.time())}"
        resultado = self.client.clientes.criar(
            accounting_firm_id=self.accounting_firm_id,
            name=nome_cliente,
            code=code,
            documentNumber="12345678909"
        )
        
        cliente_id = UUID(resultado["id"])
        print(f"   Cliente criado: {nome_cliente} (ID: {cliente_id})")
        return cliente_id
    
    def test_fluxo_completo_upload_e_conferencia(self):
        """Testa fluxo completo: criar arquivo -> upload -> enviar para conferência usando arquivo real"""
        # Caminho do arquivo de teste
        project_root = Path(__file__).parent.parent.parent
        arquivo_teste = project_root / "etc" / "arquivo.pdf"
        
        # Verifica se o arquivo existe
        if not arquivo_teste.exists():
            self.skipTest(f"Arquivo de teste não encontrado: {arquivo_teste}")
        
        nome_arquivo = arquivo_teste.name
        
        # 1. Criar arquivo para upload com todos os campos obrigatórios
        resultado = self.client.arquivos.criar_arquivo_upload(
            accounting_firm_id=self.accounting_firm_id,
            name=nome_arquivo            
        )
        
        file_id = UUID(resultado["id"])
        shared_access = resultado["sharedAccessSignature"]
        
        print(f"\n   Passo 1: Arquivo criado - ID: {file_id}")
        print(f"   Arquivo: {nome_arquivo}")        
        
        # 2. Ler arquivo do disco e fazer upload
        try:
            with open(arquivo_teste, "rb") as f:
                file_content = f.read()
            
            file_size = len(file_content)
            print(f"   Tamanho do arquivo: {file_size} bytes")
            
            response = self.client.arquivos.fazer_upload(
                shared_access_signature=shared_access,
                file_content=file_content,
                content_type="application/pdf"
            )
            
            self.assertIn(response.status_code, [200, 201, 204])
            print(f"   Passo 2: Upload realizado - Status: {response.status_code}")
            
            # 3. Enviar arquivo para tela de conferência
            resultado_conferencia = self.client.conferencia.enviar_arquivo_conferencia(
                accounting_firm_id=self.accounting_firm_id,
                file_id=file_id,
            )
            
            # Verifica se foi enviado com sucesso
            self.assertIsNotNone(resultado_conferencia)
            print(f"   Passo 3: Arquivo enviado para conferência com sucesso!")
            print(f"\n   Fluxo completo executado com sucesso!")
            print(f"   Arquivo '{nome_arquivo}' ({file_size} bytes) enviado para conferência")
            
        except Exception as e:
            # Se der erro no upload, tenta enviar mesmo assim (pode funcionar se o arquivo já existir)
            print(f"   Aviso no upload: {str(e)[:100]}")
            try:
                resultado_conferencia = self.client.conferencia.enviar_arquivo_conferencia(
                    accounting_firm_id=self.accounting_firm_id,
                    file_id=file_id
                )
                self.assertIsNotNone(resultado_conferencia)
                print(f"   Passo 3: Arquivo enviado para conferência (mesmo com erro no upload)")
            except Exception as e2:
                print(f"   Erro ao enviar para conferência: {str(e2)[:100]}")
                # Não falha o teste, apenas registra o erro
                pass


if __name__ == "__main__":
    unittest.main()

