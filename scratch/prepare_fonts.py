import urllib.request
import re
import base64
import os

os.makedirs("src/static/fonts", exist_ok=True)

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.0.0 Safari/537.36"
}

urls = {
    "Inter": "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap",
    "MaterialSymbols": "https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,0"
}

css_output = ""

for name, url in urls.items():
    print(f"Fetching CSS for {name}...")
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            css_content = response.read().decode('utf-8')
            
        font_urls = re.findall(r'url\((https://[^)]+)\)', css_content)
        for font_url in font_urls:
            print(f"Downloading font from {font_url}...")
            font_req = urllib.request.Request(font_url, headers=headers)
            with urllib.request.urlopen(font_req, timeout=5) as font_resp:
                font_data = font_resp.read()
            
            b64_data = base64.b64encode(font_data).decode('utf-8')
            fmt = "woff2"
            if ".woff" in font_url:
                fmt = "woff"
            elif ".ttf" in font_url:
                fmt = "truetype"
            
            css_content = css_content.replace(font_url, f"data:font/{fmt};base64,{b64_data}")
        
        css_output += css_content + "\n"
    except Exception as e:
        print(f"Error fetching/processing {name}: {e}")

if css_output:
    with open("src/static/fonts/offline_fonts.css", "w", encoding="utf-8") as f:
        f.write(css_output)
    print("Offline fonts CSS generated successfully at src/static/fonts/offline_fonts.css")
else:
    print("No CSS output generated.")
