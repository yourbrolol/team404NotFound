import os
import re

def get_po_msgids(po_path):
    msgids = set()
    if not os.path.exists(po_path):
        return msgids
    
    with open(po_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Simple regex to catch msgid "..."
    matches = re.findall(r'msgid\s+"(.*?)"', content)
    for m in matches:
        if m: # Ignore empty msgid "" (header)
            msgids.add(m)
    return msgids

def get_template_trans_strings(templates_dir):
    findings = {}
    
    # Regex for {% trans "..." %} or {% trans '...' %}
    trans_pattern = re.compile(r'\{%\s*trans\s+[\'"](.*?)[\'"]\s*%\}')
    # Regex for {% blocktrans %}...{% endblocktrans %}
    blocktrans_pattern = re.compile(r'\{%\s*blocktrans.*?%\}(.*?)\{%\s*endblocktrans\s*%\}', re.DOTALL)

    for root, dirs, files in os.walk(templates_dir):
        for file in files:
            if file.endswith('.html'):
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, templates_dir)
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Find all simple trans tags
                trans_matches = trans_pattern.findall(content)
                # Find all blocktrans tags (strip whitespace)
                blocktrans_matches = [m.strip() for m in blocktrans_pattern.findall(content)]
                
                all_found = set(trans_matches + blocktrans_matches)
                if all_found:
                    findings[rel_path] = all_found

    return findings

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    templates_path = os.path.join(base_dir, 'app', 'templates')
    po_path = os.path.join(base_dir, 'locale', 'uk', 'LC_MESSAGES', 'django.po')
    
    existing_ids = get_po_msgids(po_path)
    template_strings = get_template_trans_strings(templates_path)
    
    total_missing = 0
    for file, strings in template_strings.items():
        missing_in_file = [s for s in strings if s not in existing_ids]
        if missing_in_file:
            print(f"--- {file} ---")
            for s in sorted(missing_in_file):
                print(f"  [ ] \"{s}\"")
                total_missing += 1
            print()

    if total_missing == 0:
        print("✅ All translation tags in templates are already present in the .po file.")
    else:
        print(f"Found {total_missing} strings that are tagged but missing from the .po file.")
