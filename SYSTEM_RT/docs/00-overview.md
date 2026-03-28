# Visao Geral do Sistema

## Proposito
O `SYSTEM_RT` e um backend Flask para consolidar dados operacionais e financeiros vindos de provedores externos (principalmente VHSYS, Clockify e Tangerino), persistindo em banco relacional via SQLAlchemy e expondo rotas HTTP para:
- sincronizacao (`/update`) de dados externos para banco local;
- consultas paginadas e exportacao CSV;
- utilitarios de gestao de atualizacao e relatorios de apoio.

## Principais Funcionalidades
- Sincronizacao de entidades de negocio (clientes, pedidos, ordens de servico, contas, bancos, produtos, NF, etc).
- Sincronizacao de apontamentos de horas (Clockify) e ponto (Tangerino).
- Enriquecimento e cruzamento de dados para relatorios (CC, cliente por CC, estatisticas de tabelas).
- Endpoints para insercao manual de alguns registros auxiliares (ex.: `bd_assets/*`).
- Swagger UI em `/swagger` apontando para `/static/swagger.json`.

## Tecnologias
- Python + Flask
- Flask-SQLAlchemy + Flask-Migrate
- Pandas para exportacoes e transformacoes
- Requests para consumo de APIs externas
- Gunicorn para execucao em producao

## Fluxo de Alto Nivel
1. Cliente chama endpoint com `?rt_token=...`.
2. `@app.before_request` valida token.
3. Rota delega para servico local (`VHSYS_*`, `Clockify*`, `Tangerino*`, `OrdersManager`, etc).
4. Servico consulta API externa e compara com base local.
5. Banco e atualizado (insert/update), e a rota retorna status e logs resumidos.
