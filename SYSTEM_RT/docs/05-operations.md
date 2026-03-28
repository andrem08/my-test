# Guias de Operacao

## Pre-requisitos
- Python 3.x
- Banco relacional acessivel pela `DB_STRING`
- Variaveis de ambiente configuradas (`RT_TOKEN`, credenciais VHSYS/Clockify/Tangerino, etc.)

## Setup local
1. Criar ambiente virtual:
   - `python3 -m venv venv`
2. Ativar venv e instalar dependencias:
   - `source venv/bin/activate`
   - `pip install -r requirements.txt`

## Banco de dados e migrations
- Inicializar migrations:
  - `flask db init`
- Gerar/Aplicar migration:
  - `flask db migrate -m "update or db"`
  - `flask db upgrade`

## Execucao em desenvolvimento
- Script atual no repo:
  - `run-dev.bash` chama `python run.py` (verificar existencia de `run.py`; no estado atual o bootstrap principal e `app.py`).
- Forma segura:
  - `python app.py`

## Execucao estilo producao local
- `gunicorn -w 4 --timeout 10000 -b 127.0.0.1:7000 --reload app:app`

## Deploy
Nao ha pipeline de deploy declarativa no codigo lido. Baseado nos testes (`tests/test_requests_prod.py`), existe ambiente em Azure App Service.

Fluxo recomendado:
1. Aplicar migrations no ambiente alvo.
2. Configurar variaveis de ambiente/segredos.
3. Subir app WSGI com gunicorn.
4. Executar smoke tests de rotas criticas (`/orders/update`, `/os/update`, `/ov/update`, etc).

## Operacao de atualizacoes
- Use `GET /get_updated_routes` para saber as proximas rotas pendentes.
- Execute as rotas de update em lotes.
- Atualize status/output com `PUT /updated_routes_status` e `PUT /updated_route_output`.
- Ao fim, valide `GET /get_updated_routes_relation`.

## Troubleshooting rapido
- 401 em qualquer rota: conferir `rt_token` na query string.
- 500 em updates: checar credenciais de provider e formato dos dados externos.
- Erros de modelo/campo: revisar divergencias entre `models.py` e rotas/servicos.
