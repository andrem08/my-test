# Checklist: Testes, Rollback e Observabilidade

## Testes
Estado atual:
- `tests/test_requests.py`: smoke tests locais por HTTP (status `201` esperado).
- `tests/test_requests_prod.py`: smoke tests para ambiente Azure.
- `tests/test_data_conscistence.py`: consistencia entre tabelas de pedidos/OS/consolidado.

Checklist minimo antes de release:
- [ ] Rodar smoke tests locais com ambiente e tokens validos.
- [ ] Rodar subset de rotas criticas de sincronizacao em homologacao.
- [ ] Validar contagem por tabela (`GET /statistic/count`) antes/depois.
- [ ] Verificar exportacoes CSV principais.
- [ ] Verificar regressao em rotas de insercao manual.

## Rollback
Como nao ha mecanismo transacional de deploy documentado, usar rollback operacional:
- [ ] Backup/snapshot do banco antes da release.
- [ ] Versao imutavel do artifact (imagem/commit/tag).
- [ ] Procedimento de reversao da aplicacao para versao anterior.
- [ ] Procedimento de rollback de migration (quando aplicavel).
- [ ] Plano para reconciliacao de dados apos falha de sync.

## Observabilidade
Recursos atuais:
- Logs em console em varias rotas/servicos.
- Tabela `Update_route_status` para acompanhamento de execucao.
- Envio de resumo para Telegram (`utils/update_manage/telegram_manager.py`).
- Sentry presente no codigo, mas comentado em `app.py`.

Checklist recomendado:
- [ ] Reativar e configurar Sentry em todos os ambientes.
- [ ] Padronizar logs estruturados (json) com correlation id.
- [ ] Criar metricas de sucesso/erro por rota e provider.
- [ ] Alertar falhas de sincronizacao e aumento de latencia.
- [ ] Dashboard com status de rotas (`runned/not_runned`, `error_count`, duracao).
- [ ] Definir SLO minimo para rotas criticas.
