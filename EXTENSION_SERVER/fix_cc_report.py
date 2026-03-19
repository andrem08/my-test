import json

# Read file
with open('n8n_diagrams/VHSYS-cc_report-v1.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Find and fix Build Response node
for node in data['nodes']:
    if node.get('name') == 'Build Response':
        # Update jsCode to return {statusCode, body}
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
        print(f"✓ Fixed node: {node['name']}")
        break

# Save file
with open('n8n_diagrams/VHSYS-cc_report-v1.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("✓ File saved successfully")
