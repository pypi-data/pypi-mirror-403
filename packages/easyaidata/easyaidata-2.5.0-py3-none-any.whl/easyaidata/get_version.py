with open('setup.py', 'r') as f:
    content = f.read()
import re
version_match = re.search(r"version='(.*?)'", content)
if version_match:
    print(version_match.group(1))
else:
    print('2.0')
