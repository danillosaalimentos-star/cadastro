# Sistema de gestão de toners e cilindros

Programa em Python para gerenciar:

- estoque de cada modelo de toner;
- estoque de cada modelo de cilindro;
- cadastro de impressoras por departamento;
- quais modelos de toner e cilindro cada impressora utiliza.

## Requisitos

- Python 3.10+

## Uso rápido

Todos os comandos usam um banco SQLite (`toner_manager.db` por padrão).

```bash
python3 toner_manager.py add-toner "HP 58A" --estoque 12
python3 toner_manager.py add-cilindro "DR-1060" --estoque 6
python3 toner_manager.py add-departamento "Financeiro"
python3 toner_manager.py add-impressora IMP-001 "Brother HL-L5102DW" 1 1 1
python3 toner_manager.py estoque toner
python3 toner_manager.py estoque cilindro
python3 toner_manager.py impressoras
```

## Comandos

- `add-toner <nome> [--estoque N]`
- `add-cilindro <nome> [--estoque N]`
- `add-departamento <nome>`
- `add-impressora <patrimonio> <modelo> <departamento_id> <toner_model_id> <cilindro_model_id>`
- `movimentar <toner|cilindro> <model_id> <delta>`
- `estoque <toner|cilindro>`
- `impressoras`

## Observações

- `delta` em `movimentar` aceita valor positivo (entrada) e negativo (saída).
- O sistema bloqueia estoque negativo.
- IDs utilizados nos comandos são os IDs retornados nas listagens.
