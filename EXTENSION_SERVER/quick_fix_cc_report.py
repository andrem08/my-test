#!/usr/bin/env python3
import json
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Read the original file
with open('n8n_diagrams/VHSYS-cc_report-v1.json', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the problematic escape sequences by reading raw and replacing
# The issue is literal \n in the JSON that should be actual newlines

# Try to parse first
try:
    data = json.loads(content)
    print("File already valid JSON")
except json.JSONDecodeError as e:
    print(f"Found JSON error: {e}")
    print("Attempting to fix...")
    
    # Replace the problematic escaped sequences with proper ones
    # The pattern is },\n followed by \"conditions\" - this should be }, then newline then "conditions"
    
    # This is tricky - the file has literal backslash-n characters
    # We need to be very careful with the replacement
    
    # Read line by line
    lines = content.split('\n')
    
    fixed_lines = []
    for line in lines:
        # Check for the problematic pattern
        # Look for }, followed by literal \n and \" which indicates bad escaping
        
        if '},\\n' in line and '\\"' in line:
            # This line has bad escaping - split it properly
            # Split on the }, and reconstruct
            parts = line.split('},\\n')
            if len(parts) == 2:
                # Re-add the }, properly
                fixed_lines.append(parts[0] + '},')
                # Now process the remaining part - fix \" to "
                remaining = parts[1].replace('\\"', '"')
                fixed_lines.append('        ' + remaining)
            else:
                fixed_lines.append(line)
        else:
            fixed_lines.append(line)
    
    fixed_content = '\n'.join(fixed_lines)
    
    try:
        data = json.loads(fixed_content)
        print("✓ JSON fix successful!")
        
        # Now update the Build Response node
        for node in data['nodes']:
            if node.get('name') == 'Build Response' and node.get('id') == 'cc-report-response-014':
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
                print("✓ Updated Build Response node to return {statusCode, body}")
        
        # Save the file
        with open('n8n_diagrams/VHSYS-cc_report-v1.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print("✓ File saved successfully")
        
    except json.JSONDecodeError as e2:
        print(f"✗ Fix failed: {e2}")
        print("Manual intervention needed")
