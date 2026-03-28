# Seguranca

## Autenticacao
- Implementada globalmente por `@app.before_request` em `app.py`.
- Mecanismo atual: query param `rt_token` comparado com `RT_TOKEN` no ambiente.

## Autorizacao e permissoes
- Nao ha RBAC/ABAC por usuario/perfil.
- Qualquer cliente com token valido acessa todas as rotas.

## CORS
- `origins="*"`, metodos amplos (`GET, POST, PUT, DELETE`) e `supports_credentials=True`.
- Configuracao atual e permissiva e deve ser restrita em producao.

## Validacao e sanitizacao de entrada
- Sem schema validation central (ex.: Marshmallow/Pydantic).
- Sem sanitizacao explicita de strings para logs/saida.
- Conversoes numericas existem, mas sao incompletas e espalhadas.

## Riscos identificados
- Token em query string pode vazar em logs/proxies.
- Ausencia de autorizacao granular.
- Tratamento de excecao amplo com `str(e)` no retorno pode expor detalhes internos.
- CORS permissivo.

## Recomendacoes
1. Migrar autenticacao para header `Authorization: Bearer`.
2. Adicionar autorizacao por escopo/rota.
3. Introduzir validacao de payload por schema.
4. Reduzir superficie CORS para dominios confiaveis.
5. Padronizar responses de erro sem detalhes sensiveis.
6. Adicionar rate limiting e auditoria por request ID.
