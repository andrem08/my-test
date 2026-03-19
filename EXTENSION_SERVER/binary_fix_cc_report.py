#!/usr/bin/env python3
"""
Direct fix for VHSYS-cc_report-v1.json using binary read/write
"""

import json
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

input_file = 'n8n_diagrams/VHSYS-cc_report-v1.json'

print("Attempting to fix VHSYS-cc_report-v1.json...")

# Read as binary to see actual bytes
with open(input_file, 'rb') as f:
    raw_bytes = f.read()

# Convert to string
content_str = raw_bytes.decode('utf-8')

# Look for the problematic pattern: literal \n and \" sequences outside of jsCode values
# The issue is in the "conditions" object around line 77

# Try direct parse first
try:
    data = json.loads(content_str)
    print("✓ File is already valid JSON")
    is_fixed = False
except json.JSONDecodeError as e:
    print(f"✗ JSON parsing error at line {e.lineno}: {e.msg}")
    print(f"  Context: {e.doc[max(0, e.pos-50):e.pos+50]}")
    
    # Fix strategy: the problem seems to be literal\n characters in the JSON that should be newlines
    # Find the problematic lines and try to fix them
    
    lines = content_str.split('\n')
    print(f"  Total lines: {len(lines)}")
    print(f"  Problem around line: {e.lineno}")
    
    # Show context
    if e.lineno > 0 and e.lineno <= len(lines):
        print(f"  Line {e.lineno-1}: {repr(lines[e.lineno-2])}")
        print(f"  Line {e.lineno}: {repr(lines[e.lineno-1])}")
        if e.lineno < len(lines):
            print(f"  Line {e.lineno+1}: {repr(lines[e.lineno])}")
    
    # Attempt fix: look for patterns with },\n followed by \"
    # This suggests the JSON encoder put literal \n characters instead of actual newlines
    
    fixed_content = content_str
    
    # The problematic pattern is: },\n          \"conditions\":
    # It should be: },\n        "conditions":
    
    # Replace literal \n with actual newlines in problematic areas
    fixed_content = fixed_content.replace('},\\n          \\\"conditions', '},\n        "conditions')
    fixed_content = fixed_content.replace('},\\n        \\\"options', '},\n        "options')
    fixed_content = fixed_content.replace('\\n            {\\n              \\\"leftValue', '\n            {\n              "leftValue')
    fixed_content = fixed_content.replace('\\n            }\n          ]', '\n            }\n          ]')
    
    try:
        data = json.loads(fixed_content)
        print("✓ Fix successful!")
        is_fixed = True
    except json.JSONDecodeError as e2:
        print(f"✗ Fix attempt 1 failed: {e2}")
        
        # Try alternative approach - manually reconstruct the problematic section
        # by being more aggressive with replacements
        
        import re
        
        # Replace all literal \n that appear outside of quote-enclosed jsCode
        # This is risky but necessary
        
        # Strategy: find the "conditions" object section and fix it
        pattern = r'},\\n\s*\\"conditions\\"'
        replacement = '},\n        "conditions"'
        
        fixed_content = re.sub(pattern, replacement, fixed_content)
        
        try:
            data = json.loads(fixed_content)
            print("✓ Alternative fix successful!")
            is_fixed = True
        except json.JSONDecodeError as e3:
            print(f"✗ Alternative fix failed: {e3}")
            is_fixed = False

if is_fixed or 'data' in locals():
    # Now fix the Build Response node
    print("\nUpdating Build Response node...")
    
    for node in data['nodes']:
        if node.get('id') == 'cc-report-response-014' and node.get('name') == 'Build Response':
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
            print("✓ Build Response node updated")
            break
    
    # Save the fixed file
    with open(input_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print("✓ File saved successfully")
    
    # Validate
    with open(input_file, 'r', encoding='utf-8') as f:
        test_data = json.load(f)
    
    print("✓ File validation passed")
else:
    print("✗ Could not fix file - manual intervention required")
