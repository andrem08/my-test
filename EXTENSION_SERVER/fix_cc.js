const fs = require('fs');
const path = require('path');

const filepath = path.join(__dirname, 'n8n_diagrams', 'VHSYS-cc_report-v1.json');

// Read the file
const data = JSON.parse(fs.readFileSync(filepath, 'utf8'));

// Find and update the Build Response node
for (const node of data.nodes) {
  if (node.id === 'cc-report-response-014' && node.name === 'Build Response') {
    // Replace the jsCode with corrected version
    node.parameters.jsCode = `// Build success response
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
};`;
    console.log('✓ Fixed "Build Response" node');
    break;
  }
}

// Write the corrected file
fs.writeFileSync(filepath, JSON.stringify(data, null, 2), 'utf8');
console.log('✓ Saved:', filepath);
