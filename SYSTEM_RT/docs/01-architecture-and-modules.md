# Estrutura de Pastas e Modulos

## Raiz
- `app.py`: bootstrap Flask, registro de blueprints, CORS, auth por query param e configuracao DB.
- `models.py`: schema SQLAlchemy (40+ modelos).
- `requirements.txt`: dependencias.
- `run.bash`, `run-dev.bash`, `install.bash`, `initbd.bash`, `db_operations.bash`: operacao local.
- `tests/`: testes de integracao por HTTP e consistencia de dados.

## Modulos de Dominio
- `routes/`: camada HTTP (blueprints Flask).
- `VHSYS/`: integracao com API VHSYS (clientes, pedidos, OS, contas, bancos, NF, produtos, entradas, etc).
- `clockfy/`: integracao com Clockify (usuarios, clientes, projetos, tags, time entries e horas contextualizadas).
- `tangerino/`: integracao com dados de ponto e consolidacao de horas.
- `auxiliar_data/`: processamento auxiliar de HH por colaborador.
- `utils/`: managers, queries e suporte de atualizacoes.
- `log_jobs/`: logging e envio para webhook externo.
- `templates/`: template HTML (`graph.html`).

## Estrutura Logica (web/api/db)
- Web/API: `app.py` + `routes/*`.
- Servicos/providers: `VHSYS/*`, `clockfy/*`, `tangerino/*`, `auxiliar_data/*`, `utils/*`.
- Persistencia/DB: `models.py` + SQLAlchemy session (`db`).
- Observabilidade parcial: `log_jobs/*`, `utils/update_manage/*`, integracao Telegram.

## Observacao sobre Frontend
Nao ha frontend SPA (Quasar/Vue/React) neste repositorio. Nao existem `package.json`, `quasar.config.*`, `src/`, stores ou boot files de frontend.
