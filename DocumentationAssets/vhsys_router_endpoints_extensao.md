---
id: vhsys-router-endpoints-extensao
title: ⚡ VHSYS - Router de Endpoints da Extensão
sidebar_label: Router de Endpoints
description: Documentação técnica e guia de uso para o Router de Endpoints da Extensão VHSYS.
---

# Visão Geral

> **Objetivo:** Funcionar como um API Gateway (Roteador Central) que recebe requisições via webhook e as roteia para os sub-fluxos específicos com base no endpoint ou método solicitado. 

Este documento descreve o funcionamento, os requisitos e os procedimentos de resolução de problemas (debug) para o workflow **VHSYS - Router de Endpoints da Extensao**. Ele é uma peça central na arquitetura, pois gerencia as chamadas da extensão e as distribui.

---

## ⚙️ Arquitetura e Fluxo

### Gatilhos (Triggers)
- **Webhook**: O fluxo inicia a partir de um Webhook Node (`vhsys-router-webhook`), recebendo as requisições HTTP da extensão.

### Lógica Principal
1. **Webhook de Entrada**: Escuta na porta configurada e recebe o *payload* do cliente.
2. **Rotear Requisicao por Endpoint**: Um nó do tipo Switch/Router que lê a URL/Rota ou parâmetro da requisição e desvia a execução.
3. **Execução de Sub-Fluxos** (Execute Workflow):
   - `Health Check`
   - `Status CC Report` e `Gerar CC Report`
   - `Relatorio NF Venda` e `Relatorio NF Servico`
   - `Atualizar Servicos`
   - Entre outros fluxos paralelos.
4. **Validar Sucesso / Erros**: 
   - **Validar Sucesso da Resposta**: Checa o retorno do respectivo sub-fluxo.
   - **Interromper Fluxo - Erro 404 / Erro da API**: Nós que barram a execução e retornam erro adequado ao cliente.
5. **Limpeza das Esteiras**: Passos de processamento que lidam com a organização final ou coleta de lixo.

---

## 🔑 Credenciais e Configurações

Para que o workflow rode corretamente, as seguintes credenciais precisam estar configuradas no ambiente do n8n:

| Ferramenta / Nó | Tipo de Credencial | Uso no Fluxo |
| :--- | :--- | :--- |
| **Webhook** | Auth (Bearer/Basic) | Recomenda-se autenticação para que não fique exposto publicamente, ou o uso de Headers específicos para validar quem está chamando. |

---

## 🛠️ Guia de Debug e Resolução de Problemas

:::tip Como debugar
Como este é um nó central (Router), verifique **primeiro** aqui a aba de Executions para identificar para qual sub-workflow o dado foi enviado. Use o *Execution ID* para cruzar com as execuções dos nós filhos (Sub-workflows).
:::

Aqui estão os pontos críticos e os erros mais comuns mapeados para este fluxo:

### 1. Rotas Caindo em Erro 404
- **Problema**: O cliente chama o Webhook, mas o Switch manda direto para `Interromper Fluxo - Erro 404`.
- **Causa**: O parâmetro de rota enviado no corpo ou na query string não mapeia (não tem "match") com as chaves cadastradas no nó `Rotear Requisicao por Endpoint`.
- **Solução**: Valide o header / query string que a extensão está enviando. Certifique-se de que não haja erro de digitação (typo).

### 2. Timeouts ou Sub-fluxo Travado
:::danger Execuções Lentas
Se um sub-fluxo gerenciar muitos dados (ex: `Gerar CC Report`), este nó de Router ficará "pendurado" aguardando o retorno, podendo dar timeout web.
:::
- **Problema**: O webhook falha no frontend da extensão com erro 504/Timeout.
- **Causa**: O workflow filho atrelado demorou mais tempo para devolver os dados do que o limite do Webhook.
- **Solução**: Otimize o fluxo filho, adicione processamento assíncrono se necessário ou aumente o limite de timeout da plataforma/infraestrutura rodando o n8n.

### 3. Falhas na Integração (Erro da API)
- **Problema**: `Validar Sucesso da Resposta` emite erro e chama `Interromper Fluxo - Erro da API`.
- **Causa**: O workflow interno filho retornou um body contendo erro ou falhou diretamente propagando exceção.
- **Solução**: Localize de qual branch (rota) veio a requisição e abra o **Execute Workflow** específico. O erro real raramente estará aqui no Router, mas estará documentado no log do sub-fluxo.
