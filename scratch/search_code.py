import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

search_dir = 'src'
terms = ['dinh_muc_gc_phai_thuc_hien', 'so_gio_duoc_mien_giam', 'gc_vuot_thieu']

for root, dirs, files in os.walk(search_dir):
    for file in files:
        if file.endswith('.py'):
            filepath = os.path.join(root, file)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            for term in terms:
                if term in content:
                    # Find matching lines
                    lines = content.split('\n')
                    for idx, line in enumerate(lines):
                        if term in line:
                            print(f"{filepath}:{idx+1}: {line.strip()}")
