import os
import re

count = 0
for root, _, files in os.walk('src'):
    for file in files:
        if file.endswith('.py'):
            path = os.path.join(root, file)
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            new_content = re.sub(r'(?m)^(\s*)except:\s*$', r'\1except Exception:', content)
            new_content = re.sub(r'(?m)^(\s*)except:\s*pass\s*$', r'\1except Exception:\n\1    pass', new_content)
            
            if new_content != content:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                count += 1
                print(f"Updated {path}")

print(f"Total files updated: {count}")
