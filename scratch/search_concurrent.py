import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('Quy định chế độ làm việc đối với nhà giáo (Bản chuẩn toàn văn).md', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = re.finditer(r'([^\n]*kiêm nhiệm[^\n]*|[^\n]*nhiều chức vụ[^\n]*|[^\n]*nhiều chức danh[^\n]*|[^\n]*đồng thời[^\n]*)', text, re.IGNORECASE)
for m in matches:
    print(m.group(0))
