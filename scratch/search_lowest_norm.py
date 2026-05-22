import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('Quy định chế độ làm việc đối với nhà giáo (Bản chuẩn toàn văn).md', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for idx, line in enumerate(lines):
    if "kiêm nhiệm nhiều" in line or "thấp nhất" in line:
        # Print surrounding lines
        start = max(0, idx - 5)
        end = min(len(lines), idx + 6)
        print(f"--- Match at line {idx+1} ---")
        for i in range(start, end):
            print(f"{i+1}: {lines[i].strip()}")
