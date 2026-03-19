import json
import os

os.chdir(r"c:\Users\andre\.vscode\RT Projects\Extensions\EXTENSION_SERVER")

files_to_check = [
    'n8n_diagrams/VHSYS-health-v1.json',
    'n8n_diagrams/VHSYS-update_services-v1.json',
    'n8n_diagrams/VHSYS-get_update_extension_service_data-v1.json',
    'n8n_diagrams/VHSYS-cc_status-v1.json',
    'n8n_diagrams/VHSYS-cc_next_url-v1.json',
    'n8n_diagrams/VHSYS-cc_report-v1.json',
]

print("=" * 80)
print("MANUAL JSON VALIDATION")
print("=" * 80)

for file_path in files_to_check:
    print(f"\n[CHECKING] {file_path}")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"  ✓ Valid JSON")
        print(f"  - Nodes: {len(data.get('nodes', []))}")
        print(f"  - Connections: {len(data.get('connections', {}))}")
    except json.JSONDecodeError as e:
        print(f"  ✗ JSON Error at line {e.lineno}: {e.msg}")
    except FileNotFoundError:
        print(f"  ✗ File not found")
    except Exception as e:
        print(f"  ✗ Error: {e}")

print("\n" + "=" * 80)
print("END OF VALIDATION")
print("=" * 80)
