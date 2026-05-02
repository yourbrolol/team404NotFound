import os
import re

def check_i18n(templates_dir):
    categories = {
        "Missing {% load i18n %} (Uses translation tags but missing load)": [],
        "No i18n usage found (Contains hardcoded text but no translation tags)": [],
    }
    
    # Robust regex to find i18n in any load tag (e.g., {% load static i18n %})
    load_i18n_pattern = re.compile(r'\{%\s*load\s+[^%]*\bi18n\b[^%]*%\}')
    trans_usage_pattern = re.compile(r'\{%\s*(trans|blocktrans)')
    
    for root, dirs, files in os.walk(templates_dir):
        for file in files:
            if file.endswith('.html'):
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, templates_dir)
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    has_load = bool(load_i18n_pattern.search(content))
                    has_usage = bool(trans_usage_pattern.search(content))
                    
                    if not has_load and has_usage:
                        categories["Missing {% load i18n %} (Uses translation tags but missing load)"].append(rel_path)
                    elif not has_usage:
                        # Check for raw text
                        text_only = re.sub(r'<[^>]+>', '', content) 
                        text_only = re.sub(r'\{%[^%]+%\}', '', text_only)
                        text_only = re.sub(r'\{\{[^\}]+\}\}', '', text_only)
                        text_only = text_only.strip()
                        
                        if text_only and len(text_only) > 1: # Basic check to avoid stray chars
                            categories["No i18n usage found (Contains hardcoded text but no translation tags)"].append(rel_path)

    return categories

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    templates_path = os.path.join(base_dir, 'app', 'templates')
    
    print(f"Checking templates in: {templates_path}\n")
    results = check_i18n(templates_path)
    
    found_any = False
    for category, files in results.items():
        if files:
            found_any = True
            print(f"--- {category} ---")
            for f in sorted(files):
                print(f"  [!] {f}")
            print()
    
    if not found_any:
        print("✅ All templates seem to be correctly internationalized!")
