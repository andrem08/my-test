---
id: rota-api-clockify-systemrt
title: ⚡ Rota API Clockify - SystemRT
sidebar_label: Rota API Clockify
description: Documentação técnica e guia de debug para o motor de sincronização dinâmica da API do Clockify com o banco relacional.
---

# Visão Geral

> **Objetivo:** Este fluxo centraliza a extração (ETL) de diferentes entidades do Clockify (Projects, Users, Clients, Time Entries e Tags). O motor requisita paginadamente a API do Clockify usando credenciais e workspace globais, normaliza campos complexos/aninhados da API rest numa matriz tabular plana, e escreve num único disparo _(UPSERT)_ na tabela destino correspondente do banco local.

Este documento descreve detalhadamente o comportamento, os _transformers_ e as exigências para suportar o workflow **Rota API Clockify - SystemRT**.

---

## ⚙️ Arquitetura e Fluxo

### Gatilhos (Triggers)
- **Chamada Dinâmica (*Execute Workflow Output*)**: O nó `Entrada da Rota Clockify` recebe do serviço mestre um payload contendo o nome do endpoint (`url`), a tabela destino (`table`), a chave primária (`id_field`) e o Workspace ID (Opcional).

### Lógica Principal
1. **Marcar Task Pendente (PostgreSQL)**: Ativa o registro de sincronização na tabela `auxiliary.workflow_task_control` como status `1` (Em andamento) para o endpoint recebido.
2. **Buscar API Clockify (HTTP Request)**: 
   - Acessa dinamicamente a rota na versão 1 da API da Clockify (ex: `/workspaces/{workspace_id}/projects`).
   - Usa paginação em bloco (`page` iterando sequencialmente, e fixando `page-size=200`).
   - Finaliza a paginação automaticamente caso a API retorne menos de 200 resultados ou sem _body_ na última chamada.
3. **Extração e Desestruturação (Code)**: O nó `Extrair Dados Clockify` desempenha um papel massivo na padronização:
   - Recebe dados crús e os mapeia de acordo com o nome da respectiva entidade solicitada (funções `transformUsers()`, `transformTimeEntries()`, etc). 
   - Ele transforma objetos aninhados (como _Estimates_ em Projetos, ou horários _ISO_ de Time Entries) em colunas rasgadas compatíveis com a arquitetura do banco DB.
4. **Preparar Query de UPSERT (Code)**: A partir do JS, agrupa todas as propriedades sobreviventes de milhares de instâncias, criando uma query `INSERT... ON CONFLICT (id) DO UPDATE` unificada e tipando nulos para não quebrar a transação.
5. **Atualização no Banco (PostgreSQL)**: O nó `UPSERT Clockify no Banco` descarrega de vez milhões/milhares de _rows_ no _schema_ temporário correspondente (`table` do payload de entrada).
6. **Consolidações Finais (Sucesso ou Erro)**: Registram no banco (`workflow_task_control`) que o preenchimento terminou ou abortou, gerando o retorno assíncrono pro requisitor pai.

---

## 🔑 Credenciais e Configurações

Para que o workflow rode corretamente, as seguintes credenciais precisam estar configuradas no ambiente do n8n:

| Ferramenta / Nó | Tipo de Credencial | Uso no Fluxo |
| :--- | :--- | :--- |
| **Bancos de Dados PostgreSQL** | Default / SQL | Para o `UPSERT Clockify` persistir os metadados (Credencial: `Dev Database`). |
| **Buscar API Clockify (HTTP)** | Header Auth | Autentica a API através de `X-Api-Key` que deve estar setado em nome da credencial `CLOCKIFY KEY`. |

---

## 🛠️ Guia de Debug e Resolução de Problemas

:::tip Diagnosticando Mapeamento Errado
No nó central **Extrair Dados Clockify**, atente-se à cláusula `normalizeByEndpoint()`. Entidades ainda não mapeadas não terão campos organizados. Se uma query de banco falhou dizendo faltar um campo, cheque se a função de desestruturação não "renomeou" a coluna via spread.
:::

Aqui estão os pontos críticos e os erros mais comuns mapeados para este fluxo:

### 1. Loop de Paginação / Limite Excedido (API)
- **Problema**: O nó **Buscar API Clockify** trava num laço longo e exibe `Too Many Requests` ou Time-out interno (429 Too Many Requests).
- **Causa**: O tamanho _(page-size)_ requisitado somado a muitas páginas em pouco tempo estoura a franquia nominal da API. 
- **Solução**: Introduza `Batching` ou intervalo _(delay)_ a configuração do nó HTTP, ou incremente a resiliência no `retry on fail` disponível no Clockify Endpoint.

### 2. Formatação ISO de Tempo Rejeitada no Banco
- **Problema**: O Postgres emite `invalid input syntax for type interval` do objeto Clockify.
- **Causa**: Em `time_duration` ou `time_zoned`, APIs Clockify utilizam tempos em string no formato padrão `PTnHnM` (e.g. `PT3H15M` em Time Entries). Quando vai salvar no DB, ele rejeita a formatação. 
- **Solução**: Atualmente o fluxo mapeia em Segundos numéricos (`parseIsoDurationToSeconds`). Verifique se a variável está se perdendo (regex match pattern fail) ou se passou vazia (`NULL` / `undefined`).

### 3. Exceção com "Marcar Task" (Constraints)
:::danger Bloqueio de Concureência
O Postgres bloqueia inserções da fila quando já existe travamento do UPSERT (`ON CONFLICT (system, endpoint)`).
:::
- **Problema**: O nó **Marcar Task Pendente** dá erro de Database.
- **Causa**: Outra rota executou e travou a linha de log pendente da mesma entidade.
- **Solução**: Garanta a serialização primária dos cron jobs, para que entidades concorrentes de extração da mesma base (Ex: 2 robôs extraindo `users` na mesma hora) não encavalem os _deadlocks_.