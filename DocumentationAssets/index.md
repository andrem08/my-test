---
id: rt-engenharia-home
title: RT Engenharia - Automação
sidebar_label: 🏠 Início
description: Portal de Documentação Técnica e Fluxos de Automação da RT Engenharia.
slug: /
---

# 🏗️ Portal de Engenharia e Automação - RT Engenharia

Bem-vindo ao centro oficial de documentações técnicas, arquitetura de sistemas e fluxos de automação da **RT Engenharia**. 

Este portal contém todo o mapeamento arquitetural e o guia de *troubleshooting* (resolução de problemas) do nosso ecossistema de dados. Nossa infraestrutura utiliza a plataforma **n8n** como orquestrador central para consolidar dados entre os nossos principais sistemas de operação: **VHSYS** (Gestão Empresarial), **Clockify** (Gestão de Tempo) e **GLPI** (Gestão de Chamados/Helpdesk).

Aqui você encontrará a documentação completa de cada engrenagem tecnológica que suporta as operações táticas da RT Engenharia, desenhada com foco no "caminho feliz", credenciais de acesso, diagramas do pipeline de ETL e estratégias críticas para mitigação de paradas.

---

## ⚙️ 1. Orquestração e Schedulers Principais

Estes são os "motores" do nosso ecossistema. São rotinas agendadas (Cron Jobs) responsáveis por coordenar a sincronização global e garantir a integridade do Data Warehouse da RT Engenharia diariamente.

*   **[Workflow Principal de Geração de Tabelas](./workflow_principal_geracao.md)**  
    O orquestrador mestre. Configurado para rodar a cada 30 minutos de forma autônoma de segunda a sexta, disparando a cascata massiva de coleta de dados brutos (Raw Data) para atualizar o nosso repositório.
*   **[Processamento de Tabelas Auxiliares](./processar_tabelas_auxiliares.md)**  
    O sequenciador de dados derivado. Invocado após o gatilho principal, realiza leitura avançada e *seeding* (via CTE e *UPSERT* no Postgres) nas tabelas que gerenciam os diferentes status secundários operacionais da empresa.

---

## 🔌 2. Integrações via Rotas de API (Data Extractors)

Estas são as rotas ativas (conectores) que vasculham sistemas de terceiros para capturar entidades densas, lidar com paginação e registrar o histórico da RT Engenharia.

*   **[Rota API VHSYS - SystemRT](./rota_api_vhsys_systemrt.md)**  
    Fluxo de extração dinâmico de faturamentos, clientes e ordens de serviço. Converte payloads complexos e realiza *Upserts* transacionais na nossa base, atualizando também log de status.
*   **[Rota API Clockify - SystemRT](./rota_api_clockify_systemrt.md)**  
    Integração de busca relacional. Navega pelos Workspaces, Equipes e Projetos mapeando horas, convertendo métricas formatadas por strings (e.g. `PTnHnM`) em fatias temporais úteis para o banco.
*   **[Rota API Clockify Report - SystemRT](./rota_api_clockify_report_systemrt.md)**  
    Pipeline cirúrgico contra limites de processamento. Dedicado puramente aos *Detailed Reports* robustos do Clockify, segmentando pedidos por meses sequenciais a fim de estabilizar a requisição de dezenas de milhares de logs de horas laboradas por projeto na RT.
*   **[Rota API GLPI - SystemRT](./rota_api_glpi_systemrt.md)**  
    Interface com o painel de Helpdesk local da empresa. Lida com a criação de sessões seguras e captura tokens (Init Session), processando inventários ou chamados e gravando em logs SQL apartados.

---

## 🧩 3. Hub de Extensões e Ações Reativas

A automação conectada ao usuário final da RT Engenharia. Este bloco contém os webhooks disparados remotamente, na maioria das vezes, via extensões de navegação no Chrome (\Extensão VHSYS\).

*   **[Router de Endpoints da Extensão VHSYS](./vhsys_router_endpoints_extensao.md)**  
    A central de telefonia das interfaces web. Recebe uma carga unificada HTTP com comandos específicos (buscas de CC, Checkups de Saúde dos Funcionários, Consultas de Relatórios) e distribui o processamento em sub-rotinas cirúrgicas e devolve à tela do usuário na ponta final.
*   **[Extensão VHSYS - Atualizador de Status (Serviços)](./extensao_vhsys_atualizacao_status_servicos.md)**  
    Endpoint para manipulação interativa rápida. Valida regras de negócio e aciona *UPDATEs* seletivos nas bases Postgres dependendo do clique acidental ou intencional feito pelo operador através do painel na extensão do sistema do VHSYS.

---

:::tip Para a Equipe de Engenharia
Caso detecte paralisações em qualquer um desses núcleos, sua primeira checagem deve ser o ambiente **Executions do n8n**, buscando *Tags roxas* ou vermelhas (que catalogamos intensamente nesses documentos). Dê atenção redobrada ao banco de dados sempre cruzando a consistência local versus o retorno da API no nó `Workflow Task Control / Status`.
:::
