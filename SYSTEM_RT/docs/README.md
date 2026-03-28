# Documentacao SYSTEM_RT

## Indice
- `00-overview.md`: visao geral, proposito e funcionalidades.
- `01-architecture-and-modules.md`: estrutura de pastas e modulos.
- `02-backend.md`: funcionamento do backend (hooks, services, providers e DB).
- `03-frontend.md`: estado do frontend (ausente neste repo).
- `04-api-contract.md`: contrato de API extraido do codigo.
- `05-operations.md`: guia de execucao, build/deploy e operacao.
- `06-security.md`: autenticacao, autorizacao e riscos de seguranca.
- `07-testing-rollback-observability.md`: checklist operacional.
- `08-db-access-and-relations.md`: mapeamento de relacoes e acessos ao banco.
- `09-er-complete.md`: diagrama ER completo para auditoria.
- `10-uml-macroarchitecture.md`: UML macroarquitetural e fluxo operacional.

## Nota Importante
Existe `routes/hour_entry.py` com `hour_entry_route`, mas esse blueprint nao e registrado em `app.py` atualmente. Portanto, as rotas desse arquivo nao ficam ativas em runtime, salvo alteracao no bootstrap.
