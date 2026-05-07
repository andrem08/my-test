---
id: extensao-vhsys-atualizacao-status-servicos
title: ⚡ Extensão VHSYS - Atualização de Status dos Serviços
sidebar_label: Atualização de Status
description: Documentação técnica do workflow de Atualização de Status dos Serviços da Extensão VHSYS.
---

# Visão Geral

> **Objetivo:** Este workflow tem como objetivo receber chamadas (provavelmente de outros workflows ou webhooks), validar os dados de entrada e atualizar o status dos serviços no banco de dados, retornando uma resposta padronizada de sucesso ou erro.

Este documento descreve o funcionamento, os requisitos e os procedimentos de resolução de problemas (debug) para o workflow **Extensão VHSYS - Atualização de Status dos Serviços**. A documentação foi estruturada para facilitar o entendimento de como a automação deve ser operada e mantida.

---

## ⚙️ Arquitetura e Fluxo

### Gatilhos (Triggers)
- **Execução por outro Workflow / Entrada de Dados**: O fluxo inicia a partir de uma chamada interna (`Inicio do Fluxo`), recebendo dados no formato JSON.

### Lógica Principal
1. **Validar Entrada**: O nó verifica se a carga de dados de entrada possui os campos esperados e no formato correto.
2. **Dados Estão Corretos?**: Um switch/condicional que redireciona o fluxo:
   - Se **Não**: Vai para o nó **Montar Resposta de Erro**.
   - Se **Sim**: Prossegue para atualizar os dados.
3. **Atualizar Status do Serviço**: Nó principal que realiza a operação de atualização no banco de dados.
4. **Montar Resposta de Sucesso / Erro**: Formata o payload de retorno.
5. **Retornar Resposta**: Um nó `Code` final que emite a resposta consolidada para quem chamou o fluxo.

---

## 🔑 Credenciais e Configurações

Para que o workflow rode corretamente, as seguintes credenciais precisam estar configuradas no ambiente do n8n:

| Ferramenta / Nó | Tipo de Credencial | Uso no Fluxo |
| :--- | :--- | :--- |
| **Atualizar Status do Servico (Banco de Dados)** | PostgreSQL / Relacional | Usada para autenticar e persistir a atualização de status do serviço no banco. |

---

## 🛠️ Guia de Debug e Resolução de Problemas

:::tip Como debugar
Sempre verifique a aba de **Executions** no n8n. Procure pelo `Execution ID` para rastrear exatamente em qual nó o fluxo parou. O nó `Retornar Resposta` sempre trará o status consolidado.
:::

Aqui estão os pontos críticos e os erros mais comuns mapeados para este fluxo:

### 1. Falha de Validação de Entrada
- **Problema**: O fluxo é finalizado prematuramente no nó de condição `Dados Estão Corretos?` com retorno de erro.
- **Causa**: O JSON de entrada não contém as chaves obrigatórias ou está tipado incorretamente.
- **Solução**: Verifique o payload de quem está disparando a rotina. Garanta que todas as chaves exigidas no nó `Validar Entrada` estejam presentes.

### 2. Erro no Nó de Banco de Dados (`Atualizar Status do Servico`)
:::danger Alerta Banco de Dados
Quedas de conexão ou queries formadas de maneira incorreta vão gerar timeout ou erro de sintaxe SQL, paralisando essa etapa.
:::
- **Problema**: Mensagem de erro de timeout ou violação de integridade.
- **Causa**: Valores nulos passando para colunas `NOT NULL`, falha de conexão com o banco de dados.
- **Solução**: Cheque se há concorrência de atualização bloqueando a tabela ou revise as credenciais. Para debugar, injete dados mockados e valide a execução do nó individualmente.

### 3. Tratamento de Erros via nó `Code`
- **Problema**: Códigos JS falham ao montar a resposta (`Montar Resposta de Erro`).
- **Causa**: Acessar um atributo `undefined` (`$input.first().json`).
- **Solução**: Sempre verifique se o nó anterior não passou um dataset vazio. Utilize o operador `?.` (Optional Chaining) ao referenciar variáveis internas no n8n `Code` nodes.
