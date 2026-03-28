# Backend

## Inicializacao
- App Flask em `app.py`.
- Variaveis de ambiente via `.env` (`load_dotenv()`).
- DB configurado por `DB_STRING`.
- Migrations com `Flask-Migrate`.
- CORS aberto para `origins="*"`.

## Hooks
- `@app.before_request authenticate_request()`:
  - exige `rt_token` em query string;
  - compara com `RT_TOKEN` do ambiente;
  - retorna `401` em caso de divergencia.

## Blueprints/Services
As rotas geralmente seguem dois padroes:
- `PUT /.../update`: executa sincronizacao via classe de servico.
- `GET /...` ou `/.../csv`: consulta local e exporta CSV.

### Providers Externos
- VHSYS (`VHSYS/api.py` + classes `VHSYS_*`): coleta paginada, comparacao API x DB, insert/update.
- Clockify (`clockfy/*`): consumo via `X-Api-Key`, sincronizacao de usuarios/clientes/projetos/tags/time entries.
- Tangerino (`tangerino/*`): atualizacao de apontamentos/horas trabalhadas.

## Persistencia e Banco
- Todos os modelos em `models.py` (ex.: `Client`, `Pedido`, `ServiceOrder`, `Extrato`, `Clock_*`, `NF`, `Product`, tabelas auxiliares e de controle).
- Sem camada repository dedicada; as rotas/servicos usam ORM diretamente.
- Estrategia predominante de sincronizacao:
  1. carregar API externa;
  2. carregar dados locais;
  3. agrupar por chave de negocio;
  4. inserir novos e atualizar divergentes.

## Manage de atualizacoes
- `utils/update_manage/update_manager.py`:
  - controla status de rotas executadas (`Update_route_status`);
  - fornece proximas rotas para execucao (`get_not_runned_routes`);
  - envia resumo via Telegram ao concluir ciclo.

## Pontos tecnicos relevantes
- Parte das rotas retorna `201` mesmo em `GET` (nao RESTful, mas padrao atual do projeto).
- Existem inconsistencias de codigo (ex.: campos referenciados que nao existem em alguns modelos/rotas), exigindo testes de regressao antes de alterar comportamento.
