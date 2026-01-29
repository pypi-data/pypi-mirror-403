"""
Comandos CLI principais para Nibo Empresa
"""
import argparse
from .commands import (
    organizacoes,
    clientes,
    agendamentos,
    categorias,
    fornecedores
)


def main_cli():
    """Interface de linha de comando principal"""
    parser = argparse.ArgumentParser(
        description="CLI para interagir com a API Nibo Empresa",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:

  # Listar organizações
  python manage.py empresa organizacoes

  # Listar clientes
  python manage.py empresa clientes --org org_123
  python manage.py empresa clientes --nome "Empresa" --org org_123

  # Criar cliente
  python manage.py empresa criar-cliente --nome "Nova Empresa" --tipo-documento cnpj --numero-documento "12345678000190" --org org_123

  # Listar agendamentos de recebimento
  python manage.py empresa agendamentos-receber --org org_123
  python manage.py empresa agendamentos-receber --tipo vencidos --org org_123
  python manage.py empresa agendamentos-receber --cliente "Empresa" --org org_123

  # Listar agendamentos de pagamento
  python manage.py empresa agendamentos-pagar --org org_123
  python manage.py empresa agendamentos-pagar --tipo vencidos --org org_123

  # Criar agendamento de recebimento
  python manage.py empresa criar-agendamento-receber --cliente "uuid" --categoria "uuid" --valor 1000.00 --data-agendamento "01/01/2025" --data-vencimento "31/01/2025" --descricao "Recebimento" --org org_123

  # Criar agendamento de pagamento
  python manage.py empresa criar-agendamento-pagar --fornecedor "uuid" --categoria "uuid" --valor 500.00 --data-agendamento "01/01/2025" --data-vencimento "31/01/2025" --descricao "Pagamento" --org org_123

  # Listar categorias
  python manage.py empresa categorias --org org_123

  # Listar fornecedores
  python manage.py empresa fornecedores --org org_123

  # Usar formato JSON
  python manage.py empresa clientes --json --org org_123
        """
    )
    
    subparsers = parser.add_subparsers(dest="comando", help="Comandos disponíveis")
    
    # Adiciona parsers de todos os módulos de comandos
    organizacoes.add_organizacoes_parser(subparsers)
    clientes.add_clientes_parser(subparsers)
    agendamentos.add_agendamentos_parser(subparsers)
    categorias.add_categorias_parser(subparsers)
    fornecedores.add_fornecedores_parser(subparsers)
    
    # Se chamado via manage.py, remove o primeiro argumento ("empresa")
    import sys
    if len(sys.argv) > 0 and sys.argv[0].endswith("manage.py") and len(sys.argv) > 1 and sys.argv[1] == "empresa":
        # Remove "empresa" dos argumentos
        sys.argv = [sys.argv[0]] + sys.argv[2:]
    
    args = parser.parse_args()
    
    if not args.comando:
        parser.print_help()
        return 0
    
    try:
        return args.func(args)
    except Exception as e:
        print(f"ERRO: {e}")
        if hasattr(args, 'json') and args.json:
            import traceback
            traceback.print_exc()
        return 1

