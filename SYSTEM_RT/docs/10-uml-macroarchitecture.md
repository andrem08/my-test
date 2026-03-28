# UML de Macroarquitetura (Fluxo Completo)

Este diagrama resume os **contextos funcionais** do sistema e os fluxos entre API, sincronizadores, banco e observabilidade.

## 1) UML de Componentes (macroarquitetura)
```mermaid
classDiagram
  class ClienteHTTP {
    +Call endpoints com rt_token
  }

  class FlaskApp {
    +before_request(auth rt_token)
    +register blueprints
  }

  class RotasHTTP {
    +routes/*.py
    +GET/POST/PUT
  }

  class VHSYS_Sync {
    +VHSYS_* get_updates()
    +api_results()
  }

  class Clockify_Sync {
    +Clockify* get_updates()
    +hour/contexted pipelines
  }

  class Tangerino_Sync {
    +TangerinoTimeEntry.update_report()
  }

  class Auxiliares {
    +OrdersManager
    +CC managers
    +Data converters
  }

  class SQLAlchemyORM {
    +models.py
    +session add/query/commit
  }

  class PostgresDB {
    +Tabelas operacionais
    +Tabelas consolidadas
    +Tabelas controle
  }

  class Observabilidade {
    +Update_route_status
    +Telegram manager
    +Sentry (comentado)
  }

  class APIsExternas {
    +VHSYS API
    +Clockify API
    +Tangerino source
  }

  ClienteHTTP --> FlaskApp
  FlaskApp --> RotasHTTP
  RotasHTTP --> VHSYS_Sync
  RotasHTTP --> Clockify_Sync
  RotasHTTP --> Tangerino_Sync
  RotasHTTP --> Auxiliares

  VHSYS_Sync --> APIsExternas
  Clockify_Sync --> APIsExternas
  Tangerino_Sync --> APIsExternas

  VHSYS_Sync --> SQLAlchemyORM
  Clockify_Sync --> SQLAlchemyORM
  Tangerino_Sync --> SQLAlchemyORM
  Auxiliares --> SQLAlchemyORM

  SQLAlchemyORM --> PostgresDB
  RotasHTTP --> Observabilidade
  VHSYS_Sync --> Observabilidade
  Clockify_Sync --> Observabilidade
```

## 2) UML de Fluxo Operacional (pipeline de atualizacao)
```mermaid
flowchart TD
  A[Scheduler ou operador] --> B[PUT /get_updated_routes]
  B --> C[Seleciona proximas rotas]
  C --> D[Chama /.../update]
  D --> E{Contexto}

  E -->|VHSYS| F[VHSYS_* get_updates]
  E -->|Clockify| G[Clockify* get_updates]
  E -->|Tangerino| H[TangerinoTimeEntry update_report]
  E -->|Consolidacao| I[OrdersManager / CC managers]

  F --> J[Compara API x DB]
  G --> J
  H --> J
  I --> J

  J --> K[INSERT/UPDATE via SQLAlchemy]
  K --> L[(Banco de Dados)]

  K --> M[Retorno JSON logs/errors]
  M --> N[PUT /updated_routes_status]
  N --> O[PUT /updated_route_output]
  O --> P[Update_route_status]
  P --> Q{Todas rodadas?}
  Q -->|Sim| R[Resumo Telegram]
  Q -->|Nao| C
```

## 3) Contextos mapeados
- Contexto API/Web: `app.py`, `routes/*`
- Contexto Integracao VHSYS: `VHSYS/*`
- Contexto Integracao Clockify: `clockfy/*`
- Contexto Integracao Tangerino: `tangerino/*`
- Contexto RH/Auxiliar: `auxiliar_data/*`
- Contexto Consolidacao/Business: `utils/orders_manager.py`, `utils/update_cc_by_client.py`
- Contexto Controle de Execucao: `utils/update_manage/*`, tabela `Update_route_status`
- Contexto Persistencia: `models.py` + SQLAlchemy

## 4) Estados de dados na macroarquitetura
- Fonte externa: APIs VHSYS/Clockify + dataset Tangerino.
- Staging/espelho local: tabelas de dominio (`pedido`, `service_order`, `clock_*`, etc.).
- Camada consolidada: `orders_manage`, `current_worked_hours`, visoes/relatorios.
- Controle operacional: `update_route_status`, `update_cc_report_status`.
