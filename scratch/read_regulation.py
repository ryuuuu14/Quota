import re
import sys

sys.stdout.reconfigure(encoding='utf-8')
with open('Quy định chế độ làm việc đối với nhà giáo (Bản chuẩn toàn văn).md', 'r', encoding='utf-8') as f:
    content = f.read()

# Print lines containing Trần Văn B, Phạm Thị C, Bùi Thị X, Lê Văn D, Nguyễn Văn A
for name in ["Nguyễn Văn A", "Trần Văn B", "Phạm Thị C", "Lê Văn D", "Bùi Thị X"]:
    print(f"=== Matches for {name} ===")
    matches = [m.start() for m in re.finditer(re.escape(name), content)]
    for m in matches:
        start = max(0, m - 300)
        end = min(len(content), m + 500)
        print(content[start:end])
        print("-" * 50)
