---
id: workflow-principal-geracao-tabelas
title: ⚡ Workflow Principal de Geração de Tabelas
sidebar_label: Workflow Principal
description: Documentação técnica do workflow responsável pela orquestração principal, garantindo a extração de dados e a geração das tabelas em banco de dados.
---

# Visão Geral

> **Objetivo:** Este é o **Workflow Orquestrador Mestre (Scheduler)**. Sua função não é extrair dados diretamente, mas sim funcionar como o relógio/gatilho que coordena e delega toda a rotina de sincronização (ETL) e de tratamento de dados entre as APIs conectadas e o banco de dados.

Ele chama dois sub-workflows sequenciais: um dedicado exclusivamente à extração da massa de dados de várias origens para o banco local (`Fluxo para Popular Tabelas das API's`) e outro focado no tratamento e indexação secundária (`Processamento de Tabelas Auxiliares`).

---

## ⚙️ Arquitetura e Fluxo

### Gatilhos (Triggers)
- **Schedule Trigger (Cron Job)**: Executa automaticamente seguindo a expressão Cron `0 0,30 5-21 * * 1-5`. Ou seja, dispara **a cada 30 minutos** das **05:00 até 21:59**, de **Segunda a Sexta**. Nenhuma execução ocorre aos finais de semana e na janela noturna (22:00 às 04:59).
- **Manual / Webhook Trigger**: Permite o disparo sob demanda ou através de um painel de controle externo usando um URL fixo.

### Lógica Principal
1. **Ativação da Carga Base**: 
   - A execução viaja do gatilho para o nó **Chamada do Flow para popular APIs** (`executeWorkflow`).
   - Este sub-fluxo varre as rotas alvo (como VHSYS, Clockify, GLPI) e envia os metadados brutos (Raw Data) para o banco de dados. Este nó bloqueia a linha de execução (aguardando retorno) até que a carga principal seja finalizada com sucesso nas tabelas de Raw Data.
2. **Atualização da Arquitetura Auxiliar**:
   - Assim que o workflow primário de consolidação de rotas responde de volta, o segundo nó **Chamada do Flow para popular tabelas auxiliares** é engatilhado.
   - Isso garante que as tabelas acessórias (status, caches) leiam apenas das tabelas-base brutas (`raw_data`) **já atualizadas**.

---

## 🔑 Credenciais e Configurações

Para que o workflow rode corretamente, as seguintes credenciais precisam estar configuradas no ambiente do n8n:

| Ferramenta / Nó | Tipo de Credencial | Uso no Fluxo |
| :--- | :--- | :--- |
| **Nós de "Execute Workflow"** | N/A | Permissões de escopo internas no n8n. Certifique-se de que os sub-workflows pertencem ao mesmo nível/owner esperado pelo nó mestre. |

---

## 🛠️ Guia de Debug e Resolução de Problemas

:::tip Diagnóstico do Orquestrador
Por ser um orquestrador (parent workflow), 99% dos erros apontados neste nível são frutos nativos dos _child workflows_ (fluxos filhos). Use o link direto dentro do menu do nó que falhou para abrir a respectiva Execution do sub-workflow que originou a falha real.
:::

Aqui estão os pontos críticos e os erros mais comuns mapeados para este fluxo:

### 1. Parada no Meio do Processo (Timeout de Workflow)
- **Problema**: O nó "Chamada do Flow para popular APIs" fica rodando por horas ou levanta erro de timeout do sistema.
- **Causa**: Uma das tarefas do sub-fluxo (ex: Paginação profunda da Extensão VHSYS ou Clockify Report) consumiu toda a RAM do _container_ n8n ou foi enfileirada num longo delay para não estourar rate-limits das plataformas fornecedoras.
- **Solução**: Localize no histórico o _Execution ID_ de filho, descubra qual Rota de API específica gerou retardo, e trate a otimização de lá.

### 2. A Agemplementação (Schedule) não Dispara
- **Problema**: A carga parou de se atualizar automaticamente no banco nos dias de semana pela manhã.
- **Causa**: O Node do Schedule não foi habilitado (`Active` _toggle_ no topo da tela), ou as configs de timezone (`TIMEZONE` var de sistema) do servidor divergem do timezone da regra cron.
- **Solução**: Confirme se os relógios (OS do Server Docker vs n8n interface em `America/Sao_Paulo`) estão sincronizados. Assegure o uso da Cron `0 0,30 5-21 * * 1-5`.