#!/usr/bin/env python3
import subprocess
import sys
import os

os.chdir('c:\\Users\\andre\\.vscode\\RT Projects\\Extensions\\EXTENSION_SERVER')

print("=" * 80)
print("STEP 1: Running fix_cc.js")
print("=" * 80)

try:
    result = subprocess.run(['node', 'fix_cc.js'], capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    print(f"Exit code: {result.returncode}")
except Exception as e:
    print(f"Error running fix_cc.js: {e}")

print("\n" + "=" * 80)
print("STEP 2: Validating JSON files")
print("=" * 80)

# Run the validation script
result = subprocess.run(['python', 'validate_json_files.py'], capture_output=True, text=True)
print(result.stdout)
if result.stderr:
    print("STDERR:", result.stderr)
