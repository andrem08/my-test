---
id: rota-api-clockify-report-systemrt
title: ⚡ Rota API Clockify Report - SystemRT
sidebar_label: Rota API Clockify Report
description: Documentação técnica do workflow focado na extração massiva em lote de relatórios (Detailed Reports) do Clockify.
---

# Visão Geral

> **Objetivo:** O workflow **Rota API Clockify Report - SystemRT** é dedicado à persistência de "Detailed Reports" extraídos massivamente da API Reports v1 da Clockify. Diferente da rota de extração comum, este fluxo é otimizado para fatiar lapsos temporais longos (anos) em _chunks_ (lotes bimestrais) evitando estouro de timeout, normalizando os montantes cobráveis (dinheiro) e lançando as planilhas temporais _(Time Entries)_ localmente no PostgreSQL.

Este documento descreve detalhadamente o comportamento de requisição com quebra cronológica e de ingestão implementados neste workflow.

---

## ⚙️ Arquitetura e Fluxo

### Gatilhos (Triggers)
- **Chamada Dinâmica (*Execute Workflow Output*)**: A execução inicia no nó `Entrada da Rota Clockify Report`, aguardando um payload rigoroso que contenha limites estritos de data (`dateRangeStart` e `dateRangeEnd`), nome da tabela e chave primária.

### Lógica Principal
1. **Marcar Task Pendente (PostgreSQL)**: Registra no banco de dados (`workflow_task_control`) que extração iniciou rotulada ao endpoint, evitando execuções duplicadas pelo mesmo sistema.
2. **Gerar Períodos Mensais (Date Splitting)**: 
   - A API da Clockify sofre timeout se requisitada com limites longos. Para contornar, o nó **Code** lê o intervalo inicial e final, subdividindo-o em intervalos parciais de 2 meses (`STEP_MONTHS = 2`).
   - Múltiplas etapas (ítens) sairão deste nó, alimentando recursivamente a próxima etapa HTTP.
3. **Buscar API Clockify Report (HTTP POST)**:
   - Diferente dos Requests convencionais (GET), envia as fatias de datas geradas no _Body (JSON)_, definindo _Detailed Report_ com tamanho `pageSize: 1000`.
   - Inclui recurso sofisticado de cursor / numeração limitando as voltas da paginação baseada no ponteiro `totals.entriesCount` do retorno.
4. **Extrair Dados Clockify Report (Code)**:
   - Caputra a _key_ restrita `timeentries`.
   - Utilizam-se funções de higienização de tipo rigorosas para lidarem com valores fiscais: `pickMoneyAmount()` converte variáveis que podem vir como Objetos ou Strings em escalares puros `.amount` para inserção em Colunas numéricas/monetárias do BD.
5. **Preparar Query de UPSERT (Code)**: Fabrica o script SQL `WITH upserted AS (INSERT INTO ...)` lidando com potenciais conflitos através do `DO UPDATE` sobre os `id` de Report.
6. **Inserção Banco a Banco**: O nó `UPSERT Clockify Report no Banco` despacha a consulta no Database.
7. **Bifurcação Pós-Banco**: 
   - Nós de Agregação agrupam totalizadores de `rows` subindo com ou sem erro para a central (Nós _Consolidar Sucesso DB_ e _Consolidar Erros_).

---

## 🔑 Credenciais e Configurações

Para que o workflow rode corretamente, as seguintes credenciais precisam estar configuradas no ambiente do n8n:

| Ferramenta / Nó | Tipo de Credencial | Uso no Fluxo |
| :--- | :--- | :--- |
| **Buscar API Clockify Report** | Header Auth (`CLOCKIFY KEY`) | Token `X-Api-Key` que deve estar com permissão no nível de Workspace (Dono/Admins) para gerar relatórios da conta toda. |
| **PostgreSQL (Múltiplos)** | Default / SQL | Para o `UPSERT` persistir os metadados (Credencial: `Dev Database`). |

---

## 🛠️ Guia de Debug e Resolução de Problemas

:::tip Debug em Lote de Datas
Se um workflow aparentar congelado, veja os inputs do **Buscar API Clockify Report**. Ele estará disparando N vezes de acordo com o lapso temporal solicitado. Cada bloco com 1000 resultados exigirá um tempo expressivo de gravação no PostgreSQL.
:::

Aqui estão os pontos críticos e os erros mais comuns mapeados para este fluxo:

### 1. Limite ou Falha nos Relatórios `totals.entriesCount`
- **Problema**: Paginação em looping cego que não fecha e derruba a memória do Docker da n8n.
- **Causa**: Em raras instâncias de alteração no payload da Clockify, o totalizador superior (`$response.body.totals.entriesCount`) some, fazendo a expressão de terminação falhar em reconhecer o limite.
- **Solução**: Monitore as quebras da API e retorne uma contingência (ex: se result length for < 1000, force o break).

### 2. Conversão da Variável `amount` Negando
:::danger Rate/Money Mismatch
Gargalo central na função `pickMoneyAmount()` do nó de Extração.
:::
- **Problema**: Retorno PostgreSQL acusa `invalid input syntax` num insert tipicamente monetário de Rate ou Amount (`cost_amount` ou `earned_amount`).
- **Causa**: O relatório da Clockify retornou os dinheiros como objeto literal (`{ "amount": 10.0 }`) mas uma falha na interpretação JavaScript fez ele injetar no Banco um string `"[object Object]"`.
- **Solução**: Garantir que as validações de extração no nó **Extrair Dados Clockify Report** contemplaram o dado nulo recursivamente, prevenindo _crash_ em campos vazios e repassando eles como literal `NULL`.

### 3. Sobreposições Críticas (Timeout de Rede)
- **Problema**: O Nó de HTTP de Report aborta aleatoriamente gerando falha de Task.
- **Causa**: Por ser via endpoint `/reports/` (pesado computacionalmente para a própria Clockify), eles frequentemente retornam erro `502` ou `504` se o bloco (`dateRange`) é muito lotado de informações (excesso de usuários na mesma empresa em 2 meses de logs).
- **Solução**: Retroativamente, diminua a varíável de código `STEP_MONTHS` localizada no **Gerar Periodos Mensais** para _1_ (mês), esmiuçando o pedido de volta a tamanhos minúsculos que não travem a própria infra do SaaS de origem.