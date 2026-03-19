import subprocess
import sys

result = subprocess.run([sys.executable, "comprehensive_fix_validate.py"], capture_output=True, text=True)
print(result.stdout)
print(result.stderr, file=sys.stderr)
sys.exit(result.returncode)
