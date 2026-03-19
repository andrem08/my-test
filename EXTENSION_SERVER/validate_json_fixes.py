#!/usr/bin/env python3
"""Validate JSON files and check executeWorkflowTrigger conversion"""
import json
import sys
from pathlib import Path

files = [
    "n8n_diagrams/VHSYS-health-v1.json",
    "n8n_diagrams/VHSYS-update_services-v1.json",
    "n8n_diagrams/VHSYS-get_update_extension_service_data-v1.json",
    "n8n_diagrams/VHSYS-cc_status-v1.json",
    "n8n_diagrams/VHSYS-cc_next_url-v1.json",
    "n8n_diagrams/VHSYS-cc_report-v1.json",
]

print("=" * 70)
print("VALIDAÇÃO DE CORREÇÃO DOS SUBFLOWS VHSYS")
print("=" * 70)

all_valid = True
results = []

for filepath in files:
    path = Path(filepath)
    filename = path.name
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Find first node (id ending in -001)
        first_node = None
        for node in data.get('nodes', []):
            if node.get('id', '').endswith('-001'):
                first_node = node
                break
        
        if not first_node:
            results.append(f"❌ {filename}: Nenhum node com id -001 encontrado")
            all_valid = False
            continue
        
        # Check trigger type
        node_type = first_node.get('type', '')
        node_name = first_node.get('name', '')
        
        if node_type == 'n8n-nodes-base.executeWorkflowTrigger':
            if node_name == 'When called by another workflow':
                results.append(f"✅ {filename}: CORRETO")
            else:
                results.append(f"⚠️  {filename}: Tipo correto mas nome incorreto: '{node_name}'")
                all_valid = False
        elif node_type == 'n8n-nodes-base.start':
            results.append(f"❌ {filename}: ERRO - ainda usa trigger 'start'")
            all_valid = False
        else:
            results.append(f"❌ {filename}: Tipo desconhecido: {node_type}")
            all_valid = False
            
        # Check connections
        connections = data.get('connections', {})
        if 'Start' in connections:
            results.append(f"   ⚠️  Conexão 'Start' ainda existe (deve ser 'When called by another workflow')")
            all_valid = False
        elif 'When called by another workflow' in connections:
            results.append(f"   ✓ Conexões atualizadas corretamente")
        
    except json.JSONDecodeError as e:
        results.append(f"❌ {filename}: JSON INVÁLIDO - {e}")
        all_valid = False
    except Exception as e:
        results.append(f"❌ {filename}: ERRO - {e}")
        all_valid = False

print()
for result in results:
    print(result)

print()
print("=" * 70)
if all_valid:
    print("✅ TODOS OS 6 ARQUIVOS CORRIGIDOS COM SUCESSO!")
    sys.exit(0)
else:
    print("❌ ALGUMAS CORREÇÕES FALHARAM - VERIFICAR ACIMA")
    sys.exit(1)
