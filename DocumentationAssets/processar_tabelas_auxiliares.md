---
id: processar-tabelas-auxiliares
title: ⚡ Processar Tabelas Auxiliares
sidebar_label: Processar Tabelas Auxiliares
description: Documentação técnica sobre o processamento e "seeding" diário das tabelas auxiliares a partir de dados em estágio bruto.
---

# Visão Geral

> **Objetivo:** Extrair valores brutos atualizados (`raw_data`) e realizar o *seeding* (inserção inicial e sincronização contínua) nas tabelas periféricas / acessórias no schema `auxiliary`. Neste fluxo em especial, ele rastreia novos Centros de Custo (CC) criados na VHSYS e popula a tabela de "Status de Processamento do CC", a fim de garantir que integrações subsequentes saibam o que já foi lido e não processem informações repetidas.

Este documento ilustra a arquitetura de banco de dados interna usada para criar tabelas de controle via PostgreSQL dentro da automatização do n8n.

---

## ⚙️ Arquitetura e Fluxo

### Gatilhos (Triggers)
- **Quando Chamado por Outro Workflow**: Geralmente acionado pelo "Workflow Principal de Geração de Tabelas" assim que a carga base estiver completa e segura no banco.

### Lógica Principal
1. **Popular Status Processamento CC**:
   - Nó do PostgreSQL que executa um _Common Table Expression_ (CTE) `WITH source AS (...)`.
   - Consulta tudo o que há em `raw_data.vhs_centro_custos`.
   - Engatilha o insert em `auxiliary.status_processamento_cc` estabelecendo `status_entradas = 0` e `status_saidas = 0` (valores resetados/prontos para varredura) para Centros de Custos novos.
   - Executa técnica UPSERT (`ON CONFLICT... DO UPDATE`) usando o `cc_id`. Se a linha do CC já existir, ele não recria os status mas sincroniza e atualiza os selos de `data_cadastro` e `data_modificacao`, registrando o resultado em _inserted, updated, and total_ variables.
2. **Montar Resposta de Sucesso**:
   - Um nó `Code` JavaScript que emite um `console.log()` estruturado para observabilidade/telemetria.
   - Configura a saída padronizada (Cód: 201), devolvendo ao chamador o balanço contável numérico das atualizações das tabelas que ocorreram.

---

## 🔑 Credenciais e Configurações

Para que o workflow rode corretamente, as seguintes credenciais precisam estar configuradas no ambiente do n8n:

| Ferramenta / Nó | Tipo de Credencial | Uso no Fluxo |
| :--- | :--- | :--- |
| **Popular Status Processamento CC** | PostgresSQL | Chave mestre do banco de dados local (`Dev Database`) para executar _queries complexas_. |

---

## 🛠️ Guia de Debug e Resolução de Problemas

:::tip Status Zerados Diariamente?
Observe a instrução `ON CONFLICT ... DO UPDATE` dentro da SQL do nó. O status 0 só é inserido no cenário base. Em atualizações, somente as Datas são modificadas, protegendo a flag que sinaliza que foi lido. Se tudo está reajustando seus contadores para 0, veja se algo quebrou a _constraint UNIQUE_ de CC ID.
:::

Aqui estão os pontos críticos e os erros mais comuns mapeados para este fluxo:

### 1. Reversões de Tipo (Casting Errors) no SQL
- **Problema**: O nó do banco falha apresentando `invalid input syntax for type varchar...`
- **Causa**: Ao ler `vhs_centro_custos`, foi alterada a hierarquia ou tipo nativo do arquivo JSON/Tabela.
- **Solução**: O query usa `id_centro_custos::varchar`. Se a origem sofrer qualquer transição severa ou receber strings exóticas, force a limpeza no CTE `source` ou garanta o Cast mais seguro.

### 2. Retorno com Valores `Null` (Montar Resposta)
- **Problema**: O payload de resposta exibe o erro matemático `Total_ccs: NaN` ou `null`.
- **Causa**: Houve zero inserções num momento anterior por não haver dados ou query ter rodado fora do modo "Batch", fazendo com que o `COALESCE(SUM(inserted))` voltasse sem o formatador seguro embutido.
- **Solução**: Sempre use o objeto `$input.first().json || {}` no formato de chaves com `Number()` conforme está configurado no nó Code atual.

### 3. Exaustão de Pool de Conexões (*Connection Timeout*)
- **Problema**: `connectionTimeout` falho (Tempo estipulado de 30 segundos excede durante o UPSERT).
- **Causa**: Tabela de Raw Data explodindo de dados sem indexação prévia na chave original, tornando o Scan `DISTINCT` pesadíssimo.
- **Solução**: Refaça um comando de DDL via PGAdmin ou TablePlus na base dev em `raw_data.vhs_centro_custos` aplicando índice no `id_centro_custos`.