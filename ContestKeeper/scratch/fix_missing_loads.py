import os
import re

def fix_missing_loads(templates_dir):
    # Robust regex to find i18n in any load tag (e.g., {% load static i18n %})
    load_i18n_pattern = re.compile(r'\{%\s*load\s+[^%]*\bi18n\b[^%]*%\}')
    trans_usage_pattern = re.compile(r'\{%\s*(trans|blocktrans)')
    extends_pattern = re.compile(r'(\{%\s*extends\s+[^%]+\s*%\})')
    
    fixed_files = []
    
    for root, dirs, files in os.walk(templates_dir):
        for file in files:
            if file.endswith('.html'):
                file_path = os.path.join(root, file)
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                has_load = bool(load_i18n_pattern.search(content))
                has_usage = bool(trans_usage_pattern.search(content))
                
                if not has_load and has_usage:
                    # Determine where to insert {% load i18n %}
                    extends_match = extends_pattern.search(content)
                    
                    if extends_match:
                        # Insert after {% extends ... %}
                        end_pos = extends_match.end()
                        new_content = content[:end_pos] + "\n{% load i18n %}" + content[end_pos:]
                    else:
                        # Insert at the top
                        new_content = "{% load i18n %}\n" + content
                    
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    
                    fixed_files.append(os.path.relpath(file_path, templates_dir))

    return fixed_files

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    templates_path = os.path.join(base_dir, 'app', 'templates')
    
    print(f"Fixing missing i18n loads in: {templates_path}\n")
    fixed = fix_missing_loads(templates_path)
    
    if fixed:
        print(f"Successfully added '{{% load i18n %}}' to {len(fixed)} files:")
        for f in sorted(fixed):
            print(f"  [✓] {f}")
    else:
        print("No files were found that needed fixing.")
