---
id: id-do-workflow
title: ⚡ [Nome do Workflow]
sidebar_label: [Nome Curto]
description: Documentação técnica e guia de uso e debug para este workflow do n8n.
---

# Visão Geral

> **Objetivo:** [Breve descrição em linguagem simples sobre o que o workflow resolve]

Este documento descreve o funcionamento, os requisitos e os procedimentos de resolução de problemas (debug) para o workflow **[Nome do Workflow]**. A documentação foi estruturada para facilitar o entendimento de como a automação deve ser operada e mantida.

---

## ⚙️ Arquitetura e Fluxo

### Gatilhos (Triggers)
- **[Tipo de Gatilho]**: Ex: `Webhook`, `Cron / Schedule`, `Ação em App Específico`.
- **Condição de Início**: [O que exatamente dispara este fluxo]

### Lógica Principal
1. **[Passo 1]**: [Descrição da ação, ex: Busca registros no PostgreSQL]
2. **[Passo 2]**: [Descrição da transformação, ex: Formata o JSON]
3. **[Passo 3]**: [Descrição do envio, ex: Dispara requisição HTTP via API]

---

## 🔑 Credenciais e Configurações

Para que o workflow rode corretamente, as seguintes credenciais precisam estar configuradas no ambiente do n8n:

| Ferramenta / Nó | Tipo de Credencial | Uso no Fluxo |
| :--- | :--- | :--- |
| **Ex: PostgreSQL** | Nome da Credencial BD | Leitura e escrita de logs/dados |
| **Ex: HTTP Request** | Header Auth (Bearer) | Autenticação em API externa |

---

## 🛠️ Guia de Debug e Resolução de Problemas

:::tip Como debugar
Sempre verifique a aba de **Executions** no n8n. Procure pelo `Execution ID` para rastrear exatamente em qual nó o fluxo parou.
:::

Aqui estão os pontos críticos e os erros mais comuns mapeados para este fluxo:

### 1. Falha de Conexão ou Timeout (APIs/Banco)
* **Sintoma:** O nó `HTTP Request` ou o nó de Banco de Dados falha com erro de timeout ou conexão recusada.
* **Ação:** Verifique se as credenciais estão ativas e se a rede não está bloqueando o IP da instância do n8n. Valide a estrutura de dados (ex: colunas ausentes no banco).

### 2. Erro de Mapeamento de Dados (Data Mapping)
* **Sintoma:** Um nó retorna `[ERROR] Cannot read properties of undefined`.
* **Ação:** Inspecione o JSON do nó anterior. O formato da resposta da API pode ter mudado, ou um campo esperado veio nulo. Utilize um nó `Code` (JavaScript) intermediário para tratar campos vazios, se necessário.

### 3. Loop Infinito ou Limite de Paginação
* **Sintoma:** O workflow consome muita memória ou entra em loop longo.
* **Ação:** Revise a lógica do nó de loop (ex: `Loop` node). Garanta que a condição de saída (`Break`) está recebendo o critério de parada correto na manipulação dos arrays.

---

## 📝 Histórico de Alterações

- **[Data]**: Implementação inicial e documentação técnica