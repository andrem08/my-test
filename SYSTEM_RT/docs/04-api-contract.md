# Contrato de API (extraido do codigo)

Base path: `/`
Autenticacao global: query param obrigatorio `rt_token` em todas as rotas (hook `before_request`).
Erro padrao: `{ "error": "..." }` com HTTP `500` em exceptions.

## Health/Root
- `GET /`
  - Entrada: nenhuma alem de `rt_token`.
  - Saida: string `Hello from {CONTEXT}!`.
  - Status: `200`.

## Sincronizacao VHSYS / Clockify / Tangerino
- `PUT /orders/update` -> atualiza tabela consolidada de pedidos/OS (`OrdersManager`).
- `PUT /os/update` -> sincroniza ordens de servico VHSYS.
- `PUT /ov/update` -> sincroniza pedidos VHSYS.
- `PUT /extract/update` -> sincroniza extrato VHSYS.
- `PUT /client/update` -> sincroniza clientes VHSYS.
- `PUT /cc/update` -> sincroniza centros de custo VHSYS.
- `PUT /category/update` -> sincroniza categorias VHSYS.
- `PUT /banks/update` -> sincroniza bancos VHSYS.
- `PUT /account_payment/update` -> sincroniza contas a pagar VHSYS.
- `PUT /account_inputs/update` -> sincroniza contas a receber VHSYS.
- `PUT /buy_order/update` -> sincroniza ordens de compra VHSYS.
- `PUT /nf/update` -> sincroniza notas fiscais.
- `PUT /products` -> sincroniza cadastro de produtos.
- `PUT /merch_products` -> sincroniza itens/produtos de entradas.
- `PUT /merch_entry` -> sincroniza entradas de mercadorias.
- `PUT /clock/clock_user/update` -> sincroniza usuarios Clockify.
- `PUT /clock/clock_client/update` -> sincroniza clientes Clockify.
- `PUT /clock/clock_project/update` -> sincroniza projetos Clockify.
- `PUT /clock/tags/update` -> sincroniza tags Clockify.
- `PUT /clock/clock_entry/update` -> sincroniza apontamentos Clockify.
- `PUT /contexted_hours` -> gera/atualiza horas contextualizadas (Clockify + regras internas).
- `PUT /contexted_hours_prima` -> atualiza horas contextualizadas de base Prima.
- `PUT /tagerino/time_entry` -> atualiza base Tangerino.
- `PUT /auxiliar_data/employer_hh/update` -> atualiza HH de empregadores.

Saida tipica (sync): objeto JSON de resumo, geralmente com `message`, `logs`, `error`.
Status tipico: `201`.

## Consulta e exportacao
- `GET /os?page=&per_page=` -> lista paginada de ordens de servico.
- `GET /os/csv` -> CSV de ordens de servico.
- `GET /extract?page=&per_page=` -> lista paginada de extratos.
- `GET /extract/csv` -> CSV de extratos.
- `GET /client?page=&per_page=` -> lista paginada de clientes.
- `GET /client/csv` -> CSV de clientes.
- `GET /cc?page=&per_page=` -> lista paginada de centros de custo.
- `GET /cc/ids` -> ids de centros de custo.
- `GET /cc/all` -> lista completa de centros de custo.
- `GET /cc/csv` -> CSV de centros de custo.
- `GET /buy_order/` -> CSV de ordens de compra.
- `GET /clock/clock_client` -> CSV de clientes Clockify.
- `GET /clock/clock_project` -> CSV de projetos Clockify.
- `GET /clock/clock_user` -> lista paginada (implementacao atual com possivel inconsistencias de campos).
- `GET /clock/clock_user/csv` -> CSV de usuarios Clockify.
- `GET /clock/clock_entry` -> CSV de time entries.
- `GET /clock/prima_entry` -> CSV de base Prima.
- `GET /clock/clock_api` -> retorno com payload CSV e `content_type` nao padrao.
- `GET /prima_entries` -> CSV de PrimaData.
- `GET /view/orders` -> visao consolidada de pedidos/OS.
- `GET /view/orders/csv` -> CSV da visao de pedidos/OS.
- `GET /view/cc_report_total` -> executa query de relatorio CC e retorna array.
- `GET /view/client_by_cc_info` -> mapeamento CC x cliente.
- `GET /view/userInfo` -> mapeamento usuario Clockify x cliente.
- `GET /statistic/count` -> contagem de linhas por tabela.

## Insercao manual/auxiliar
- `POST /os/new`
  - Body JSON obrigatorio com campos de `ServiceOrder` usados em `create_order`.
- `POST /extract/new`
  - Body JSON obrigatorio com campos de `Extrato` usados em `create_extract`.
- `POST /client/new`
  - Body JSON obrigatorio com campos de `Client` usados na rota.
- `POST /cc/new`
  - Body JSON obrigatorio com campos de `CentroCustos` usados na rota.
- `POST /pedido/new`
  - Body JSON obrigatorio com campos de `Pedido` usados na rota.
- `POST /clock/clock_user/new`
  - Body JSON: `id`, `email`, `name`, `profile_pic`, `active_workspace`, `default_workspace`.
- `PUT /clock/clock_user/edit`
  - Body JSON parcial para atualizar os mesmos campos.
- `POST /clock/prima`
  - Body JSON da estrutura `PrimaData`.
- `POST /clock/hour_entry`
  - Body JSON no formato retornado pela API Clockify (`id`, `timeInterval`, etc.).
- `POST /client_by_cc/new`
  - Body JSON para criar associacao (implementacao atual espera `CC`, `PROJETO`, `CLIENT`).
- `POST /cc_report/new_entry_by_id`
  - Body JSON aceito, mas logica de persistencia ainda nao implementada.
- `POST /bd_assets/valor_base_by_cargo/new`
  - Body JSON: `cargo`, `valor_base`.
- `POST /bd_assets/name_equivalence/new`
  - Body JSON: `user`, `user_name`.
- `POST /bd_assets/index_year/new`
  - Body JSON: `ano`, `fator`.
- `POST /bd_assets/colaborador_cargo/new`
  - Body JSON: `colaborador`, `ativo`, `categoria`, `adm`, `momento_inicio_cargo`, `momento_fim_cargo`, `cargo_atual`.
- `POST /prima_entry/new`
  - Body JSON no formato `PrimaData`.

## Gestao de status de rotas
- `GET /route_manager_info` -> dump da tabela `Update_route_status`.
- `GET /get_updated_routes` -> proximas rotas pendentes.
- `GET /get_updated_routes_relation` -> resumo runned x not_runned.
- `PUT /updated_routes_status`
  - Body JSON: `{ "route": "..." }`.
- `PUT /updated_route_output`
  - Body JSON: `{ "route": "...", "start": ..., "end": ..., "logs_count": ..., "error_count": ... }`.
- `PUT /reset_updated_routes_status` -> reseta status.

## Validacoes observadas
- Validacao principal: token via query string.
- Validacoes de payload: majoritariamente implicitas (acesso direto `data["campo"]`), sem schema central.
- Conversoes numericas manuais (`verify_numeric_int/float`) em varios modulos.
