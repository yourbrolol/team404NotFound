import os
import re

def cleanup_i18n(templates_dir):
    # Matches exactly what we added: {% load i18n %} followed by a newline
    added_load_tag = "{% load i18n %}\n"
    # Matches any load tag containing i18n
    any_load_i18n_pattern = re.compile(r'\{%\s*load\s+[^%]*\bi18n\b[^%]*%\}')
    
    cleaned_files = []
    
    for root, dirs, files in os.walk(templates_dir):
        for file in files:
            if file.endswith('.html'):
                file_path = os.path.join(root, file)
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Find all occurrences of load tags with i18n
                matches = list(any_load_i18n_pattern.finditer(content))
                
                if len(matches) > 1:
                    # We have multiple loads. Let's see if one is the simple one we added.
                    # We look for "{% load i18n %}" specifically.
                    
                    # If we find both "{% load i18n %}" and another one like "{% load static i18n %}",
                    # we remove the simple "{% load i18n %}".
                    
                    has_simple = "{% load i18n %}" in content
                    has_combined = any("{% load" in m.group(0) and "i18n" in m.group(0) and m.group(0) != "{% load i18n %}" for m in matches)
                    
                    if has_simple and has_combined:
                        # Remove the simple one + trailing newline if it exists
                        new_content = content.replace("{% load i18n %}\n", "", 1)
                        # Just in case there was no newline
                        if new_content == content:
                            new_content = content.replace("{% load i18n %}", "", 1)
                            
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(new_content)
                        cleaned_files.append(os.path.relpath(file_path, templates_dir))

    return cleaned_files

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    templates_path = os.path.join(base_dir, 'app', 'templates')
    
    print(f"Cleaning up redundant i18n loads in: {templates_path}\n")
    cleaned = cleanup_i18n(templates_path)
    
    if cleaned:
        print(f"Successfully removed redundant '{{% load i18n %}}' from {len(cleaned)} files:")
        for f in sorted(cleaned):
            print(f"  [✓] {f}")
    else:
        print("No redundant loads found.")
