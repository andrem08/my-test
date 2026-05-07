---
id: rota-api-glpi-systemrt
title: ⚡ Rota API GLPI - SystemRT
sidebar_label: Rota API GLPI
description: Documentação técnica e guia de debug para a integração da API do GLPI (Gestão de chamados).
---

# Visão Geral

> **Objetivo:** Este workflow tem como objetivo consolidar as regras de conexão, extração e _UPSERT_ com a API do sistema GLPI. Diferente de outras APIs (que usam apenas um Bearer Token), o GLPI exige uma etapa prévia de inicialização de sessão (via `/initSession`) para capturar um `Session-Token` temporário usado nas requisições subsequentes.

Este documento detalha o comportamento da arquitetura do *handshake* da API do GLPI acompanhado do fluxo de gravação nas tabelas de banco correspondentes.

---

## ⚙️ Arquitetura e Fluxo

### Gatilhos (Triggers)
- **Chamada Dinâmica (*Execute Workflow Output*)**: A execução começa no nó `Entrada da Rota GLPI`, onde as variáveis determinantes da extração (`url`, `table`, `id_field`) são recebidas de _workflows_ pai ou schedulers mestre.

### Lógica Principal
1. **Marcar Task Pendente (PostgreSQL)**: Bloqueia ou sinaliza na tabela de controle que o _sync_ da respectiva entidade GLPI iniciou (`status = 1`).
2. **Inicializar Sessão (`GLPI Iniciar Sessão`)**:
   - Faz uma chamada HTTP GET/POST nativa do GLPI em `/initSession`.
   - Gera e devolve um Session-Token temporário.
   - Em caso de falha de comunicação, despacha o processo para `Formatar Erro Init Session GLPI`, matando o fluxo prematuramente.
3. **Requisição aos Dados (`Buscar API GLPI`)**: 
   - Atinge dinamicamente a `url` solicitada (ex: `Ticket`, `User`, `Computer`).
   - Transita as chaves fixas pre-definidas acopladas ao recém obtido `Session-Token` no Header.
4. **Higienização do Retorno (`Extrair Dados GLPI`)**: Um nó de código JavaScript responsável por achatar as respostas da API, que podem vir puramente como um Array de objetos `[{}, {}]` ou encapsulados como `{ data: [] }`. 
5. **Gerador de Instrução (`Preparar UPSERT GLPI`)**: Extrai as colunas válidas da resposta, escapando caracteres especiais para não quebrar a sintaxe do _Postgres_ e montando a string SQL de `INSERT... ON CONFLICT(...) DO UPDATE`.
6. **Gravação e Gestão de Status**:
   - Dispara o SQL diretamente no PostgreSQL (`UPSERT GLPI no Banco`).
   - Avalia a variável `affected_rows` para garantir o sucesso real do log, bifurcando as anotações gerenciais entre erro e sucesso devolvendo a resposta para quem deu o Trigger.

---

## 🔑 Credenciais e Configurações

Para que o workflow rode corretamente, as seguintes credenciais precisam estar configuradas no ambiente do n8n:

| Ferramenta / Nó | Tipo de Credencial | Uso no Fluxo |
| :--- | :--- | :--- |
| **GLPI Iniciar Sessão** | HTTP Multiple Headers (`GLPI Auth`) | Necessária para gerar a sessão de login inicial via rest baseada geralmente em um `Authorization: Basic` local. |
| **Buscar API GLPI** | HTTP Header Auth (`GLPI App Token`) | Refere-se à credencial de App (App-Token) comum do GLPI exigida conjuntamente na maioria das chamadas _REST_. |
| **PostgreSQL (Múltiplos)** | Default / SQL (`Dev Database`) | Exigida nos nós de UPSERT para inserção de log e metadados. |

---

## 🛠️ Guia de Debug e Resolução de Problemas

:::tip Diagnosticando Bloqueios de App-Token
O GLPI tem políticas de segurança bem rígidas sobre os IPs que solicitam as APIs. Se encontrar timeouts ou erros _403/401_ no nó **GLPI Iniciar Sessão**, verifique se o servidor do GLPI não bloqueou o endereço de IP do servidor do n8n.
:::

Aqui estão os pontos críticos e os erros mais comuns mapeados para este fluxo:

### 1. Perda de Session Token (Erro de Sessão)
- **Problema**: O Nó **Buscar API GLPI** falha dizendo `Session token missing or invalid`.
- **Causa**: A conexão de sessão no primeiro Nó excedeu limite de concorrência imposto pelo cliente GLPI para o mesmo usuário, ou a política de uso de sessão do GLPI local derrubou o token recém-criado.
- **Solução**: Ative o tempo de re-tentativa (`retryOnFail`) nos nós da HTTP GLPI ou configure via Painel Administrativo do GLPI uma tolerância maior de _API session concurrency_.

### 2. Retorno Limpo sem Registros Rejeitando SQL
:::danger Alerta Banco de Dados Quebrado
APIs rest de entidades nativas raras muitas vezes retornam `{}` em vez de listagens.
:::
- **Problema**: O Fluxo cai num branch de _Erro DB_ alegando erro de Parse ao tentar ler o objeto.
- **Causa**: O Node `Extrair Dados GLPI` desativou o mapeamento achando que tinha conteúdo mas na verdade era uma String vazia ou Error Text proveniente da chamada 200 Ok.
- **Solução**: Checar no log de falha de _UPSERT_ qual instrução ele compôs no Node de _Preparo_ e blindar os checkups locais no Javascript caso `length === 0`. Felizmente, o bloco base possui o fallback retornando `SELECT 0::int affected_rows`, contanto que retorne _Array_.

### 3. Problema no ID Primário (GLPI não segue padrão total)
- **Problema**: O sistema PostgreSQL rejeita dizendo `column "uuid" does not exist`.
- **Causa**: Quando o Trigger envia a carga, ele especifica uma _Primary Key_ (ex: `id_ticket`), mas o endpoint do GLPI daquela entidade usa simplesmente a chave `id` que choca com _upsert_.
- **Solução**: Sempre observe do lado que manda a execução do _Trigger_ se o parâmetro `id_field` passado condiz exatamente com o nome da chave literal principal retornada do JSON do GLPI.