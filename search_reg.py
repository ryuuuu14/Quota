import sys
sys.stdout.reconfigure(encoding='utf-8')

# Search for teacher names or "Ví dụ 1" / "Ví dụ 2" in the regulation
with open('Quy định chế độ làm việc đối với nhà giáo (Bản chuẩn toàn văn).md', 'r', encoding='utf-8') as f:
    lines = f.readlines()

def search_terms(terms):
    print(f"Searching for: {terms}")
    for idx, line in enumerate(lines):
        for term in terms:
            if term.lower() in line.lower():
                print(f"Line {idx+1}: {line.strip()}")
                break

search_terms(["Lê Văn D", "Bùi Thị X", "Nguyễn Văn A", "Trần Văn B", "Phạm Thị C"])
