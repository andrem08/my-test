import json
import sys

files_to_fix = [
    'n8n_diagrams/VHSYS-cc_report-v1.json'
]

for filepath in files_to_fix:
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Simple string replacement for Build Response node
        old_return = '"return {\\n  message: \'CC_REPORT processed successfully\',\\n  cc_id: diff.cc_id,\\n  type: diff.type,\\n  inserted: diff.to_insert.length,\\n  deleted: diff.to_delete.length\\n};"'
        new_return = '"return {\\n  statusCode: 200,\\n  body: {\\n    message: \'CC_REPORT processed successfully\',\\n    cc_id: diff.cc_id,\\n    type: diff.type,\\n    inserted: diff.to_insert.length,\\n    deleted: diff.to_delete.length\\n  }\\n};"'
        
        if old_return in content:
            content = content.replace(old_return, new_return)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✓ Fixed: {filepath}")
        else:
            print(f"⚠ Pattern not found in: {filepath}")
            
    except Exception as e:
        print(f"✗ Error with {filepath}: {e}")
        sys.exit(1)

print("\n✓ All fixes completed")
