#!/usr/bin/env python3
import json
import os
import sys

# Files to validate
files_to_check = [
    'n8n_diagrams/VHSYS-health-v1.json',
    'n8n_diagrams/VHSYS-update_services-v1.json',
    'n8n_diagrams/VHSYS-get_update_extension_service_data-v1.json',
    'n8n_diagrams/VHSYS-cc_status-v1.json',
    'n8n_diagrams/VHSYS-cc_next_url-v1.json',
    'n8n_diagrams/VHSYS-cc_report-v1.json',
]

print("=" * 80)
print("JSON VALIDATION AND SUBFLOW VERIFICATION")
print("=" * 80)

results = {
    'valid_json': [],
    'invalid_json': [],
    'issues': []
}

for file_path in files_to_check:
    full_path = os.path.join(os.getcwd(), file_path)
    print(f"\n[CHECKING] {file_path}")
    
    # Check if file exists
    if not os.path.exists(full_path):
        print(f"  ✗ File not found: {full_path}")
        results['invalid_json'].append(file_path)
        continue
    
    # Try to parse JSON
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"  ✓ Valid JSON")
        results['valid_json'].append(file_path)
    except json.JSONDecodeError as e:
        print(f"  ✗ Invalid JSON: {str(e)}")
        results['invalid_json'].append(file_path)
        results['issues'].append(f"{file_path}: JSON Parse Error - {str(e)}")
        continue
    except Exception as e:
        print(f"  ✗ Error reading file: {str(e)}")
        results['invalid_json'].append(file_path)
        results['issues'].append(f"{file_path}: Read Error - {str(e)}")
        continue
    
    # Check for Start node (not Webhook)
    nodes = data.get('nodes', [])
    has_start_node = False
    has_webhook_node = False
    has_respond_to_webhook = False
    last_code_node = None
    
    for node in nodes:
        node_type = node.get('type', '')
        node_name = node.get('name', '')
        node_id = node.get('id', '')
        
        # Check for Start node
        if node_type == 'n8n-nodes-base.start':
            has_start_node = True
            print(f"  ✓ Has Start node: {node_id}")
        
        # Check for Webhook node
        if 'webhook' in node_type.lower():
            has_webhook_node = True
            print(f"  ⚠ Found Webhook node: {node_id} ({node_type})")
        
        # Check for respondToWebhook nodes
        if 'respondToWebhook' in node_type or 'respond-to-webhook' in node_type.lower():
            has_respond_to_webhook = True
            print(f"  ✗ Found respondToWebhook node: {node_id} ({node_type})")
        
        # Track code nodes to check the last one
        if node_type == 'n8n-nodes-base.code':
            last_code_node = {
                'id': node_id,
                'name': node_name,
                'jsCode': node.get('parameters', {}).get('jsCode', ''),
                'typeVersion': node.get('typeVersion', 0)
            }
    
    # Check if Start node exists
    if not has_start_node:
        results['issues'].append(f"{file_path}: Missing Start node")
        print(f"  ✗ Missing Start node")
    
    # Check if respondToWebhook exists
    if has_respond_to_webhook:
        results['issues'].append(f"{file_path}: Contains respondToWebhook node(s)")
        print(f"  ✗ Contains respondToWebhook node(s)")
    
    # Check last code node returns {statusCode, body}
    if last_code_node:
        js_code = last_code_node['jsCode']
        if 'statusCode' in js_code and 'body' in js_code:
            print(f"  ✓ Last code node returns {{statusCode, body}}: {last_code_node['id']}")
        else:
            results['issues'].append(f"{file_path}: Last code node doesn't return {{statusCode, body}}")
            print(f"  ✗ Last code node doesn't return {{statusCode, body}}: {last_code_node['id']}")
            print(f"    Code preview: {js_code[:100]}...")
    else:
        results['issues'].append(f"{file_path}: No code nodes found")
        print(f"  ⚠ No code nodes found")

# Summary
print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"\n✓ Valid JSON files: {len(results['valid_json'])}")
for f in results['valid_json']:
    print(f"  - {f}")

if results['invalid_json']:
    print(f"\n✗ Invalid JSON files: {len(results['invalid_json'])}")
    for f in results['invalid_json']:
        print(f"  - {f}")

if results['issues']:
    print(f"\n⚠ Issues found: {len(results['issues'])}")
    for issue in results['issues']:
        print(f"  - {issue}")
else:
    print(f"\n✓ No issues found!")

sys.exit(0 if not results['issues'] and not results['invalid_json'] else 1)
