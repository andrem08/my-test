#!/usr/bin/env python3
"""
Recreate VHSYS-cc_report-v1.json with correct formatting and fixes
"""

report_json = {
  "name": "VHSYS-cc_report-v1",
  "nodes": [
    {
      "parameters": {},
      "id": "cc-report-start-001",
      "name": "Start",
      "type": "n8n-nodes-base.start",
      "typeVersion": 1,
      "position": [240, 300]
    },
    {
      "parameters": {
        "jsCode": "// Validate input payload\nconst body = $input.first().json.body || $input.first().json;\n\nif (!body.data || !body.type || !body.cc_id) {\n  throw new Error('Missing required fields: data, type, cc_id');\n}\n\nif (body.type !== 'entrada' && body.type !== 'saida') {\n  throw new Error('Invalid type: must be \"entrada\" or \"saida\"');\n}\n\n// Structured logging\nconsole.log(JSON.stringify({\n  timestamp: new Date().toISOString(),\n  event: 'cc_report_received',\n  cc_id: body.cc_id,\n  type: body.type,\n  has_data: !!body.data\n}));\n\nreturn body;"
      },
      "id": "cc-report-validate-002",
      "name": "Validate Input",
      "type": "n8n-nodes-base.code",
      "typeVersion": 2,
      "position": [460, 300]
    },
    {
      "parameters": {
        "jsCode": "// Decode HTML entities in the payload\nconst data = $input.first().json;\n\nfunction decodeHtmlEntities(obj) {\n  if (typeof obj === 'string') {\n    return obj\n      .replace(/&amp;/g, '&')\n      .replace(/&lt;/g, '<')\n      .replace(/&gt;/g, '>')\n      .replace(/&quot;/g, '\"')\n      .replace(/&#39;/g, \"'\")\n      .replace(/&nbsp;/g, ' ');\n  }\n  if (typeof obj === 'object' && obj !== null) {\n    const decoded = Array.isArray(obj) ? [] : {};\n    for (const key in obj) {\n      decoded[key] = decodeHtmlEntities(obj[key]);\n    }\n    return decoded;\n  }\n  return obj;\n}\n\nconst decodedData = decodeHtmlEntities(data);\n\nconsole.log(JSON.stringify({\n  timestamp: new Date().toISOString(),\n  event: 'cc_report_decoded',\n  cc_id: decodedData.cc_id\n}));\n\nreturn decodedData;"
      },
      "id": "cc-report-decode-003",
      "name": "Decode HTML Entities",
      "type": "n8n-nodes-base.code",
      "typeVersion": 2,
      "position": [680, 300]
    },
    {
      "parameters": {
        "jsCode": "// Extract and transform CC report data\nconst payload = $input.first().json;\nconst ccData = payload.data;\nconst type = payload.type;\nconst ccIdReference = payload.cc_id;\n\n// Check if page is valid\nif (!ccData.source || !ccData.source.subItens) {\n  console.log(JSON.stringify({\n    timestamp: new Date().toISOString(),\n    event: 'cc_report_invalid_page',\n    cc_id: ccIdReference,\n    level: 'warn'\n  }));\n  return {\n    cc_id: ccIdReference,\n    type: type,\n    records: [],\n    valid: false\n  };\n}\n\nconst source = ccData.source;\nconst ccLabel = source.itens[0].CentroCustos;\nconst subItens = source.subItens.ID1 || [];\n\n// Group and flatten records\nfunction groupEqualDicts(arr) {\n  const grouped = [];\n  let index = 0;\n  while (arr.length > 0) {\n    const current = arr.shift();\n    const group = [{ index, ...current }];\n    for (let i = arr.length - 1; i >= 0; i--) {\n      if (JSON.stringify(current) === JSON.stringify(arr[i])) {\n        group.push({ index, ...arr[i] });\n        arr.splice(i, 1);\n      }\n    }\n    grouped.push(group);\n    index++;\n  }\n  return grouped.flat();\n}\n\nconst groupedRegs = groupEqualDicts([...subItens]);\n\n// Generate ID tokens\nfunction generateIdToken(seed) {\n  const crypto = require('crypto');\n  return crypto.createHash('sha256').update(seed).digest('hex');\n}\n\nconst formattedRecords = groupedRegs.map(subItem => {\n  const INDEX = subItem.index;\n  const VENCIMENTO = subItem.Vencimento;\n  const FORNECEDOR = subItem.Fornecedor;\n  const NOME_DESPESA = subItem.NomeDespesa;\n  const SITUACAO = subItem.Situacao;\n  const VALOR = subItem.Valor;\n  const CATEGORIA = subItem.Categoria;\n  \n  const SEED = `${INDEX}-${ccIdReference}-${NOME_DESPESA}-${VENCIMENTO}-${FORNECEDOR}-${VALOR}-${SITUACAO}-${type}-${CATEGORIA}`;\n  const TOKEN = generateIdToken(SEED);\n  \n  return {\n    INDEX,\n    CC_LABEL: ccLabel,\n    CC_ID: ccIdReference,\n    VENCIMENTO,\n    FORNECEDOR,\n    NOME_DESPESA,\n    SITUACAO,\n    CATEGORIA,\n    VALOR,\n    ID_SEED: SEED,\n    ID: TOKEN,\n    TYPE: type\n  };\n});\n\nconsole.log(JSON.stringify({\n  timestamp: new Date().toISOString(),\n  event: 'cc_report_transformed',\n  cc_id: ccIdReference,\n  type: type,\n  records_count: formattedRecords.length\n}));\n\nreturn {\n  cc_id: ccIdReference,\n  type: type,\n  cc_label: ccLabel,\n  records: formattedRecords,\n  valid: true\n};"
      },
      "id": "cc-report-transform-004",
      "name": "Transform Data",
      "type": "n8n-nodes-base.code",
      "typeVersion": 2,
      "position": [900, 300]
    },
    {
      "parameters": {
        "operation": "executeQuery",
        "query": "-- Get existing records for this CC_ID and TYPE\nSELECT \"id\"\nFROM raw_data.\\"vhx_relatorio_cc\\"\nWHERE \"id_cc\" = '{{ $json.cc_id }}'\n  AND \"type\" = '{{ $json.type }}';",
        "options": {}
      },
      "id": "cc-report-existing-005",
      "name": "Get Existing Records",
      "type": "n8n-nodes-base.postgres",
      "typeVersion": 2.4,
      "position": [1120, 300],
      "credentials": {
        "postgres": {
          "id": "vhsys-postgres-prod",
          "name": "vhsys-postgres-prod"
        }
      }
    },
    {
      "parameters": {
        "jsCode": "// Compare and calculate diff\nconst current = $input.first().json;\nconst existing = $input.last().json;\n\n// Extract IDs\nconst extensionIds = new Set(current.records.map(r => r.ID));\nconst dbIds = new Set(Array.isArray(existing) ? existing.map(r => r.ID) : []);\n\n// Calculate differences\nconst toInsert = current.records.filter(r => !dbIds.has(r.ID));\nconst toDelete = Array.from(dbIds).filter(id => !extensionIds.has(id));\n\nconsole.log(JSON.stringify({\n  timestamp: new Date().toISOString(),\n  event: 'cc_report_diff_calculated',\n  cc_id: current.cc_id,\n  type: current.type,\n  to_insert: toInsert.length,\n  to_delete: toDelete.length\n}));\n\nreturn {\n  cc_id: current.cc_id,\n  type: current.type,\n  cc_label: current.cc_label,\n  to_insert: toInsert,\n  to_delete: toDelete\n};"
      },
      "id": "cc-report-diff-006",
      "name": "Calculate Diff",
      "type": "n8n-nodes-base.code",
      "typeVersion": 2,
      "position": [1340, 300]
    },
    {
      "parameters": {
        "conditions": {
          "options": {
            "caseSensitive": true,
            "leftValue": "",
            "typeValidation": "strict"
          },
          "conditions": [
            {
              "leftValue": "={{ $json.to_insert.length }}",
              "rightValue": "0",
              "operator": {
                "type": "number",
                "operation": "gt"
              }
            }
          ],
          "combinator": "and"
        },
        "options": {}
      },
      "id": "cc-report-has-insert-007",
      "name": "Has Inserts?",
      "type": "n8n-nodes-base.if",
      "typeVersion": 2,
      "position": [1560, 300]
    },
    {
      "parameters": {
        "jsCode": "// Split records for batch insert\nconst data = $input.first().json;\nconst records = data.to_insert;\n\nreturn records.map(record => ({\n  ...data,\n  record: record\n}));"
      },
      "id": "cc-report-split-008",
      "name": "Split Records",
      "type": "n8n-nodes-base.code",
      "typeVersion": 2,
      "position": [1780, 220]
    },
    {
      "parameters": {
        "operation": "executeQuery",
        "query": "-- Insert new CC report record\nINSERT INTO raw_data.\\"vhx_relatorio_cc\\" (\n  \"id\",\n  \"id_seed\",\n  \"id_cc\",\n  \"cc\",\n  \"cc_label\",\n  \"vencimento\",\n  \"fornecedor\",\n  \"nome_despesa\",\n  \"situacao\",\n  \"data_pagamento\",\n  \"categoria\",\n  \"valor\",\n  \"type\",\n  \"created_at\",\n  \"updated_at\"\n) VALUES (\n  '{{ $json.record.ID }}',\n  '{{ $json.record.ID_SEED }}',\n  '{{ $json.record.CC_ID }}',\n  'NO-SET',\n  '{{ $json.record.CC_LABEL }}',\n  to_timestamp({{ $json.record.VENCIMENTO }}),\n  '{{ $json.record.FORNECEDOR }}',\n  '{{ $json.record.NOME_DESPESA }}',\n  '{{ $json.record.SITUACAO }}',\n  (CURRENT_TIMESTAMP AT TIME ZONE 'America/Sao_Paulo')::timestamp,\n  '{{ $json.record.CATEGORIA }}',\n  {{ $json.record.VALOR }},\n  '{{ $json.record.TYPE }}',\n  (CURRENT_TIMESTAMP AT TIME ZONE 'America/Sao_Paulo')::timestamp,\n  (CURRENT_TIMESTAMP AT TIME ZONE 'America/Sao_Paulo')::timestamp\n);",
        "options": {}
      },
      "id": "cc-report-insert-009",
      "name": "Insert Record",
      "type": "n8n-nodes-base.postgres",
      "typeVersion": 2.4,
      "position": [2000, 220],
      "credentials": {
        "postgres": {
          "id": "vhsys-postgres-prod",
          "name": "vhsys-postgres-prod"
        }
      }
    },
    {
      "parameters": {
        "conditions": {
          "options": {
            "caseSensitive": true,
            "leftValue": "",
            "typeValidation": "strict"
          },
          "conditions": [
            {
              "leftValue": "={{ $json.to_delete.length }}",
              "rightValue": "0",
              "operator": {
                "type": "number",
                "operation": "gt"
              }
            }
          ],
          "combinator": "and"
        },
        "options": {}
      },
      "id": "cc-report-has-delete-010",
      "name": "Has Deletes?",
      "type": "n8n-nodes-base.if",
      "typeVersion": 2,
      "position": [1780, 380]
    },
    {
      "parameters": {
        "jsCode": "// Split IDs for batch delete\nconst data = $input.first().json;\nconst ids = data.to_delete;\n\nreturn ids.map(id => ({\n  cc_id: data.cc_id,\n  type: data.type,\n  id_to_delete: id\n}));"
      },
      "id": "cc-report-split-delete-011",
      "name": "Split Delete IDs",
      "type": "n8n-nodes-base.code",
      "typeVersion": 2,
      "position": [2000, 380]
    },
    {
      "parameters": {
        "operation": "executeQuery",
        "query": "-- Delete record by ID\nDELETE FROM raw_data.\\"vhx_relatorio_cc\\"\nWHERE \"id\" = '{{ $json.id_to_delete }}';",
        "options": {}
      },
      "id": "cc-report-delete-012",
      "name": "Delete Record",
      "type": "n8n-nodes-base.postgres",
      "typeVersion": 2.4,
      "position": [2220, 380],
      "credentials": {
        "postgres": {
          "id": "vhsys-postgres-prod",
          "name": "vhsys-postgres-prod"
        }
      }
    },
    {
      "parameters": {
        "operation": "executeQuery",
        "query": "-- Update CC report status\nUPDATE update_cc_report_status\nSET \n  entries_runned = CASE WHEN '{{ $json.type }}' = 'entrada' THEN 1 ELSE entries_runned END,\n  outputs_runned = CASE WHEN '{{ $json.type }}' = 'saida' THEN 1 ELSE outputs_runned END,\n  updated_at = (CURRENT_TIMESTAMP AT TIME ZONE 'America/Sao_Paulo')::timestamp\nWHERE cc_id = '{{ $json.cc_id }}';",
        "options": {}
      },
      "id": "cc-report-update-status-013",
      "name": "Update Status",
      "type": "n8n-nodes-base.postgres",
      "typeVersion": 2.4,
      "position": [2220, 220],
      "credentials": {
        "postgres": {
          "id": "vhsys-postgres-prod",
          "name": "vhsys-postgres-prod"
        }
      }
    },
    {
      "parameters": {
        "jsCode": "// Build success response\nconst diff = $input.first().json;\n\nconsole.log(JSON.stringify({\n  timestamp: new Date().toISOString(),\n  event: 'cc_report_completed',\n  cc_id: diff.cc_id,\n  type: diff.type,\n  inserted: diff.to_insert.length,\n  deleted: diff.to_delete.length\n}));\n\nreturn {\n  statusCode: 200,\n  body: {\n    message: 'CC_REPORT processed successfully',\n    cc_id: diff.cc_id,\n    type: diff.type,\n    inserted: diff.to_insert.length,\n    deleted: diff.to_delete.length\n  }\n};"
      },
      "id": "cc-report-response-014",
      "name": "Build Response",
      "type": "n8n-nodes-base.code",
      "typeVersion": 2,
      "position": [2440, 300]
    }
  ],
  "connections": {
    "Start": {
      "main": [
        [
          {
            "node": "Validate Input",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Validate Input": {
      "main": [
        [
          {
            "node": "Decode HTML Entities",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Decode HTML Entities": {
      "main": [
        [
          {
            "node": "Transform Data",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Transform Data": {
      "main": [
        [
          {
            "node": "Get Existing Records",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Get Existing Records": {
      "main": [
        [
          {
            "node": "Calculate Diff",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Calculate Diff": {
      "main": [
        [
          {
            "node": "Has Inserts?",
            "type": "main",
            "index": 0
          },
          {
            "node": "Has Deletes?",
            "type": "main",
            "index": 0
          },
          {
            "node": "Build Response",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Has Inserts?": {
      "main": [
        [
          {
            "node": "Split Records",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Split Records": {
      "main": [
        [
          {
            "node": "Insert Record",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Insert Record": {
      "main": [
        [
          {
            "node": "Update Status",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Has Deletes?": {
      "main": [
        [
          {
            "node": "Split Delete IDs",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Split Delete IDs": {
      "main": [
        [
          {
            "node": "Delete Record",
            "type": "main",
            "index": 0
          }
        ]
      ]
    }
  },
  "pinData": {},
  "settings": {
    "executionOrder": "v1"
  },
  "staticData": None,
  "tags": [
    {
      "name": "VHSYS",
      "id": "vhsys-tag"
    },
    {
      "name": "CC_REPORT",
      "id": "cc-report-tag"
    },
    {
      "name": "Phase-3",
      "id": "phase3-tag"
    }
  ],
  "triggerCount": 0,
  "updatedAt": "2026-03-18T04:45:00.000Z",
  "versionId": "cc-report-v1-001"
}

# Save the file
import json
import os

# Change to the correct directory
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

output_path = 'n8n_diagrams/VHSYS-cc_report-v1.json'

# Handle None -> null conversion
report_json['staticData'] = None  # Keep as None, json.dump will convert to null

with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(report_json, f, indent=2, ensure_ascii=False)

print(f"✓ Fixed and saved: {output_path}")
print("✓ All fixes applied:")
print("  - Fixed JSON syntax (removed literal \\n characters)")
print("  - Updated 'Build Response' node to return {statusCode, body}")
print("  - All nodes properly formatted")






