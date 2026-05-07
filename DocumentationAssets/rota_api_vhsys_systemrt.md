---
id: rota-api-vhsys-systemrt
title: ⚡ Rota API VHSYS - SystemRT
sidebar_label: Rota API VHSYS
description: Documentação técnica e guia de debug para a integração (ETL) da API VHSYS.
---

# Visão Geral

> **Objetivo:** Esta rota atua como um fluxo ETL dinâmico para a API da VHSYS. Ela recebe dinamicamente um endpoint (ex: `ordens-servico`), faz a extração dos dados paginados da API, estrutura as queries e faz um Insert/Update (UPSERT) na tabela correspondente do banco de dados, controlando o status da execução via tabela auxiliar.

Este documento descreve o funcionamento, os requisitos e os procedimentos de resolução de problemas (debug) para o workflow **Rota API VHSYS - SystemRT**. A documentação foi estruturada para facilitar o entendimento de como a automação deve ser operada e gerida.

---

## ⚙️ Arquitetura e Fluxo

### Gatilhos (Triggers)
- **Chamada de Outro Workflow**: Inicia com o nó `Entrada da Rota VHSYS` (`executeWorkflowTrigger`), que recebe as definições e variáveis do endpoint (como `url`, `table`, `id_field`, etc.).

### Lógica Principal
1. **Marcar Task Pendente**: Regista ou atualiza a tabela `auxiliary.workflow_task_control` no PostgreSQL, indicando que a carga do sistema (VHSYS) e endpoint iniciou (`status = 1`).
2. **Buscar API VHSYS**: 
   - Interage via requisição HTTP com a API da VHSYS (`https://api.vhsys.com/v2/{{ endpoint }}`).
   - Possui paginação configurada automaticamente (buscando 250 itens por página através de `offset` e `limit`), rodando até esgotar o `total` de registros retornado na reposta.
   - Em caso de falha de conexão, encaminha para rotina de erro.
3. **Extrair Dados VHSYS**: Nó intermédio (`Code`) que consolida as múltiplas páginas retornadas num único array de objetos manipulável.
4. **Preparar UPSERT VHSYS**: Um bloco de script avançado que lê as chaves extraídas dos objetos (pulando atributos internos) e monta uma instrução SQL dinamicamente: `INSERT INTO ... ON CONFLICT (...) DO UPDATE`. Este nó também trata _edge cases_ incômodos, como converter a data `0000-00-00` em `NULL` ou fazer strings complexas tornarem-se compatíveis.
5. **UPSERT VHSYS no Banco**: Dispara o comando SQL construído na tabela alvo.
6. **Controlo de Falha ou Sucesso**:
   - **Caminho de Sucesso**: Agrega o resultado das inserções, atualiza a execução para completo (`status = 2`) em `workflow_task_control` e gera o payload limpo apontando sucesso.
   - **Caminho de Falha (DB / API)**: Registra log de erro na base e emite output de falha (`status = -1`).

---

## 🔑 Credenciais e Configurações

Para que o workflow rode corretamente, as seguintes credenciais precisam estar configuradas no ambiente do n8n:

| Ferramenta / Nó | Tipo de Credencial | Uso no Fluxo |
| :--- | :--- | :--- |
| **Marcar Task / UPSERT no Banco** | PostgresSQL | Lidar com chamadas e escritas na base local de ETL (`Dev Database`). |
| **Buscar API VHSYS** | HTTP Multiple Headers Auth | Token/Chaves em formato Headers (`VHSYS Auth Token`) para acesso à API Rest. |

---

## 🛠️ Guia de Debug e Resolução de Problemas

:::tip Como debugar
Sempre que uma execução principal apontar erro no banco, consulte os retornos dos nós **Formatar Erro API VHSYS** ou **Resultado Erro DB VHSYS**. O `Execution ID` mostrará exatamente a query produzida ou a falha de HTTP correspondente.
:::

Aqui estão os pontos críticos e os erros mais comuns mapeados para este fluxo:

### 1. Paginação Infinita ou Timeout HTTP (Buscar API VHSYS)
- **Problema**: O nó trava rodando sem parar, gastando a memória máxima ou estourando limite de tempo de HTTP.
- **Causa**: A lógica condicional final de repetição falhou em ler se `offset + limit >= total` (ex: a API VHSYS alterou o payload ou omitiu a chave `paging.total`).
- **Solução**: Valide com uma requisição base isolada a estrutura json devolvida, confirmando se os atributos `data` ou `.paging` permanecem iguais. Verifique limites contratuais da API da VHSYS (Rate Limits).

### 2. Conversão e Limpeza de Dados Quebrando o UPSERT
:::danger Query Quebrada em "Preparar UPSERT"
Textos não prevenidos adequadamente com aspas (ex: nomes de clientes, caracteres invisíveis) ou datas incompatíveis.
:::
- **Problema**: O nó `UPSERT VHSYS no Banco` relata `syntax error at or near...`.
- **Causa**: A injeção de parâmetros pode ter esbarrado numa _string_ com apóstrofo solto ou caractere não escapatório para SQL vindo diretamente da resposta da VHSYS.
- **Solução**: Adicione lógica de escape (`.replace()`) em `toSql(v)` na função customizada localizada em `Preparar UPSERT VHSYS`. Se a coluna está a tentar engolir data inconsistente extra (além de `0000-00` já tratado), reforce a regex para ignorar nulos.

### 3. A Tabela Alvo Não Existe (DB Sync)
- **Problema**: `relation "raw_data.vhs_alguma_coisa" does not exist`.
- **Causa**: O workflow chamador enviou uma chave via Trigger solicitando salvar em uma tabela física ou ID Primário (`id_field`) que não foram criados no PostgreSQL.
- **Solução**: Checar e criar a DDL (`CREATE TABLE raw_data...`) no Postgres de antemão ou garantir que a chave `table` apontada corresponde estritamente ao banco.