import os
import urllib.request
import re

# Create directories
os.makedirs("static/fonts", exist_ok=True)

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.0.0 Safari/537.36"
}

# 1. Process Inter CSS
with open("scratch/inter_test.css", "r", encoding="utf-8") as f:
    inter_css = f.read()

# We want to replace each URL with local file and download it
inter_urls = re.findall(r'url\((https://[^)]+)\)', inter_css)
weights = [400, 500, 600, 700, 800]

for idx, url in enumerate(inter_urls):
    weight = weights[idx] if idx < len(weights) else 400
    local_filename = f"inter-{weight}.ttf"
    local_path = os.path.join("static/fonts", local_filename)
    
    print(f"Downloading Inter {weight} from {url}...")
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            with open(local_path, "wb") as lf:
                lf.write(resp.read())
        print(f"Saved to {local_path}")
        # Replace in CSS
        inter_css = inter_css.replace(url, f"/app/static/fonts/{local_filename}")
    except Exception as e:
        print(f"Failed to download {url}: {e}")

# 2. Process Material CSS
with open("scratch/material_test.css", "r", encoding="utf-8") as f:
    material_css = f.read()

# We only need the 400 weight (the 4th url in the list or matching weight 400)
# Let's find the URL for weight 400
# Line 23 of material_test.css contains weight 400 url:
# https://fonts.gstatic.com/s/materialsymbolsoutlined/v343/kJF1BvYX7BgnkSrUwT8OhrdQw4oELdPIeeII9v6oDMzByHX9rA6RzaxHMPdY43zj-jCxv3fzvRNU22ZXGJpEpjC_1v-p_4MrImHCIJIZrDCvHOem.ttf
material_url = "https://fonts.gstatic.com/s/materialsymbolsoutlined/v343/kJF1BvYX7BgnkSrUwT8OhrdQw4oELdPIeeII9v6oDMzByHX9rA6RzaxHMPdY43zj-jCxv3fzvRNU22ZXGJpEpjC_1v-p_4MrImHCIJIZrDCvHOem.ttf"
local_filename = "material-symbols-outlined.ttf"
local_path = os.path.join("static/fonts", local_filename)

print(f"Downloading Material Symbols Outlined from {material_url}...")
try:
    req = urllib.request.Request(material_url, headers=headers)
    with urllib.request.urlopen(req, timeout=15) as resp:
        with open(local_path, "wb") as lf:
            lf.write(resp.read())
    print(f"Saved to {local_path}")
except Exception as e:
    print(f"Failed to download Material Symbols: {e}")

# Create offline material css
offline_material_css = f"""@font-face {{
  font-family: 'Material Symbols Outlined';
  font-style: normal;
  font-weight: 400;
  src: url('/app/static/fonts/{local_filename}') format('truetype');
}}

.material-symbols-outlined {{
  font-family: 'Material Symbols Outlined';
  font-weight: normal;
  font-style: normal;
  font-size: 24px;
  line-height: 1;
  letter-spacing: normal;
  text-transform: none;
  display: inline-block;
  white-space: nowrap;
  word-wrap: normal;
  direction: ltr;
}}
"""

# Combine into static/fonts.css
with open("static/fonts.css", "w", encoding="utf-8") as f:
    f.write(inter_css)
    f.write("\n")
    f.write(offline_material_css)

print("Offline static/fonts.css generated successfully!")
