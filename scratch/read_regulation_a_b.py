import re
import sys

sys.stdout.reconfigure(encoding='utf-8')
with open('Quy định chế độ làm việc đối với nhà giáo (Bản chuẩn toàn văn).md', 'r', encoding='utf-8') as f:
    content = f.read()

for name in ["Nguyễn Văn A", "Trần Văn B"]:
    print(f"=== Matches for {name} ===")
    matches = [m.start() for m in re.finditer(re.escape(name), content)]
    if not matches:
        print("No matches found.")
    for m in matches:
        start = max(0, m - 300)
        end = min(len(content), m + 500)
        print(content[start:end])
        print("-" * 50)
