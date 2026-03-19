import json

# Read the file
filepath = r'c:\Users\andre\.vscode\RT Projects\Extensions\EXTENSION_SERVER\n8n_diagrams\VHSYS-cc_report-v1.json'

with open(filepath, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Find and update the Build Response node
for node in data['nodes']:
    if node.get('id') == 'cc-report-response-014' and node.get('name') == 'Build Response':
        # Replace the jsCode with corrected version
        node['parameters']['jsCode'] = """// Build success response
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
        print(f"✓ Fixed 'Build Response' node")
        break

# Write the corrected file
with open(filepath, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"✓ Saved: {filepath}")
