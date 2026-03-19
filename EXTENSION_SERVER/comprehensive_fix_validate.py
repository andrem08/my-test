#!/usr/bin/env python3
"""
Comprehensive fix and validation script for n8n JSON files
1. Fixes JSON syntax issues in cc_report file
2. Updates Build Response nodes to return {statusCode, body}
3. Validates all JSON files
"""

import json
import os
import sys
import re

def fix_json_syntax(file_path):
    """Fix common JSON syntax issues"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix: replace literal \n in JSON strings with proper escape sequences
    # This is a tricky fix that looks for unescaped newlines in parameter values
    # The issue is likely in the 'conditions' object where \n appears literally
    
    # Try to parse first
    try:
        data = json.loads(content)
        return data, False  # No fix needed
    except json.JSONDecodeError as e:
        print(f"  JSON Parse Error at line {e.lineno}: {e.msg}")
        
        # Fix attempt: look for the problematic pattern and fix it
        # The pattern seems to be: },\n          \"conditions\": 
        # This needs to be: },\n          \"conditions\": (properly formatted)
        
        lines = content.split('\n')
        
        # Try to rebuild the JSON more carefully
        # Look for lines that have literal \n that shouldn't be there
        fixed_lines = []
        for i, line in enumerate(lines):
            # Check if line has \n that's not part of a JSON string
            if '\\n' in line and '"' not in line.split('\\n')[0]:
                # This looks like a literal \n outside of strings - this is wrong
                fixed_lines.append(line.replace('},\\n', '},'))
            else:
                fixed_lines.append(line)
        
        fixed_content = '\n'.join(fixed_lines)
        
        try:
            data = json.loads(fixed_content)
            return data, True  # Fix was successful
        except json.JSONDecodeError:
            return None, False  # Fix didn't work

def validate_json_file(file_path):
    """Validate JSON file and return parsed data"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data, True, None
    except json.JSONDecodeError as e:
        return None, False, str(e)
    except Exception as e:
        return None, False, str(e)

def check_subflow_requirements(data, file_path):
    """Check if subflow meets all requirements"""
    issues = []
    
    if not data or 'nodes' not in data:
        issues.append("No nodes found in workflow")
        return issues
    
    nodes = data['nodes']
    has_start_node = False
    has_respond_to_webhook = False
    last_code_node = None
    code_nodes = []
    
    for node in nodes:
        node_type = node.get('type', '')
        node_name = node.get('name', '')
        node_id = node.get('id', '')
        
        if node_type == 'n8n-nodes-base.start':
            has_start_node = True
        
        if 'respondToWebhook' in node_type or 'respond-to-webhook' in node_type.lower():
            has_respond_to_webhook = True
            issues.append(f"Found respondToWebhook node: {node_id}")
        
        if node_type == 'n8n-nodes-base.code':
            code_nodes.append({
                'id': node_id,
                'name': node_name,
                'jsCode': node.get('parameters', {}).get('jsCode', ''),
                'position': code_nodes.__len__()
            })
    
    if not has_start_node:
        issues.append("Missing Start node (type: n8n-nodes-base.start)")
    
    if has_respond_to_webhook:
        issues.append("Contains respondToWebhook node(s)")
    
    # Check last code node
    if code_nodes:
        last_code_node = code_nodes[-1]
        js_code = last_code_node['jsCode']
        
        # Check if returns {statusCode, body}
        if 'statusCode' not in js_code or 'body' not in js_code:
            issues.append(f"Last code node '{last_code_node['name']}' doesn't return {{statusCode, body}}")
        else:
            # Check structure more carefully
            if not ('return {' in js_code and 'statusCode' in js_code):
                issues.append(f"Last code node '{last_code_node['name']}' doesn't properly return {{statusCode, body}}")
    else:
        issues.append("No code nodes found")
    
    return issues

# Main execution
print("=" * 80)
print("JSON SUBFLOW FIX AND VALIDATION")
print("=" * 80)

os.chdir(os.path.dirname(os.path.abspath(__file__)))

files_to_check = [
    'n8n_diagrams/VHSYS-health-v1.json',
    'n8n_diagrams/VHSYS-update_services-v1.json',
    'n8n_diagrams/VHSYS-get_update_extension_service_data-v1.json',
    'n8n_diagrams/VHSYS-cc_status-v1.json',
    'n8n_diagrams/VHSYS-cc_next_url-v1.json',
    'n8n_diagrams/VHSYS-cc_report-v1.json',
]

files_fixed = []
validation_results = {}

print("\n[STEP 1] Validating and fixing JSON syntax\n")

for file_path in files_to_check:
    print(f"[CHECKING] {file_path}")
    
    if not os.path.exists(file_path):
        print(f"  ✗ File not found")
        validation_results[file_path] = {'json_valid': False, 'error': 'File not found'}
        continue
    
    # Try to validate JSON
    data, is_valid, error = validate_json_file(file_path)
    
    if not is_valid:
        print(f"  ⚠ JSON syntax issues detected")
        # Try to fix
        fixed_data, was_fixed = fix_json_syntax(file_path)
        if fixed_data:
            data = fixed_data
            is_valid = True
            files_fixed.append(file_path)
            print(f"  ✓ JSON fixed")
        else:
            print(f"  ✗ Could not fix: {error}")
            validation_results[file_path] = {'json_valid': False, 'error': error}
            continue
    else:
        print(f"  ✓ Valid JSON")
    
    validation_results[file_path] = {'json_valid': True, 'error': None}

print("\n[STEP 2] Running fix scripts\n")

# Run fix_cc.js equivalent (Python version for fix_cc_report.py)
try:
    print("[Running] fix_cc_report.py equivalent...")
    cc_report_path = 'n8n_diagrams/VHSYS-cc_report-v1.json'
    
    with open(cc_report_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    for node in data['nodes']:
        if node.get('name') == 'Build Response' and node.get('id') == 'cc-report-response-014':
            # Update jsCode to return {statusCode, body}
            new_code = """// Build success response
const diff = $input.first().json;

console.log(JSON.stringify({
  timestamp: new Date().toISOString(),
  event: 'cc_report_completed',
  cc_id: diff.cc_id,
  type: diff.type,
  inserted: diff.to_insert.length,
  deleted: diff.to_delete.length
}));

return {
  statusCode: 200,
  body: {
    message: 'CC_REPORT processed successfully',
    cc_id: diff.cc_id,
    type: diff.type,
    inserted: diff.to_insert.length,
    deleted: diff.to_delete.length
  }
};"""
            node['parameters']['jsCode'] = new_code
            print(f"  ✓ Fixed 'Build Response' node")
            
            # Save the file
            with open(cc_report_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"  ✓ Saved: {cc_report_path}")
            break
except Exception as e:
    print(f"  ✗ Error: {e}")

print("\n[STEP 3] Validating subflow requirements\n")

all_issues = {}
for file_path in files_to_check:
    if file_path not in validation_results or not validation_results[file_path]['json_valid']:
        continue
    
    print(f"[CHECKING] {file_path}")
    
    # Load the file
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        issues = check_subflow_requirements(data, file_path)
        
        if not issues:
            print(f"  ✓ All requirements met")
        else:
            print(f"  ⚠ Issues found:")
            for issue in issues:
                print(f"    - {issue}")
            all_issues[file_path] = issues
        
        validation_results[file_path]['subflow_valid'] = len(issues) == 0
        validation_results[file_path]['issues'] = issues
    except Exception as e:
        print(f"  ✗ Error checking: {e}")
        validation_results[file_path]['subflow_valid'] = False
        validation_results[file_path]['issues'] = [str(e)]

# Summary report
print("\n" + "=" * 80)
print("SUMMARY REPORT")
print("=" * 80)

print(f"\n✓ Files Fixed: {len(files_fixed)}")
for f in files_fixed:
    print(f"  - {f}")

valid_json_files = [f for f, r in validation_results.items() if r.get('json_valid')]
print(f"\n✓ Valid JSON Files: {len(valid_json_files)}/{len(files_to_check)}")

if all_issues:
    print(f"\n⚠ Files with Issues: {len(all_issues)}")
    for file_path, issues in all_issues.items():
        print(f"  {file_path}:")
        for issue in issues:
            print(f"    - {issue}")
else:
    print(f"\n✓ All files pass validation!")

sys.exit(0 if not all_issues else 1)
