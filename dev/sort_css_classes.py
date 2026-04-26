import os
import sys
import re

def sort_css_file(css_path):
    if not os.path.exists(css_path):
        return

    with open(css_path, 'r') as f:
        content = f.read()

    # Look for the extraction comment marker
    marker_match = re.search(r'/\* --- Extracted from .*? ---\s*\*/', content)
    
    if not marker_match:
        return # Skip if it doesn't have extracted styles
    
    marker_pos = marker_match.end()
    
    # We will sort everything after the marker.
    header_content = content[:marker_match.start()]
    marker_content = marker_match.group(0)
    extra_content = content[marker_pos:]
    
    # Find all simple single-line CSS rules we appended: ".tag-001 { ... }"
    # We strip empty lines and extract the rules
    lines = extra_content.strip().split('\n')
    
    rules = []
    other_lines = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Check if it matches our pattern ".classname { ... }"
        match = re.match(r'^(\.[a-z0-9-]+)\s*\{.*?\}$', line)
        if match:
            rules.append({
                'class': match.group(1),
                'line': line
            })
        else:
            other_lines.append(line)
            
    if not rules:
        return
        
    # Sort the rules based on the class name alphabetically and numerically
    def sort_key(rule_dict):
        cls_name = rule_dict['class']
        # Try to split into text and number part: .div-001 -> 'div', 1
        m = re.match(r'^\.([a-z-]+)-(\d+)$', cls_name)
        if m:
            return (m.group(1), int(m.group(2)))
        return (cls_name, 0)
        
    rules.sort(key=sort_key)
    
    # Reconstruct the file content
    new_extra_content = "\n" + marker_content + "\n"
    if other_lines:
        new_extra_content += "\n".join(other_lines) + "\n\n"
        
    new_extra_content += "\n".join(r['line'] for r in rules) + "\n"
    
    with open(css_path, 'w') as f:
        f.write(header_content.rstrip() + "\n\n" + new_extra_content.strip() + "\n")
        
    print(f"Sorted {len(rules)} classes in {os.path.basename(css_path)}")

def find_css_files():
    project_root = "/mnt/data/Documents/Projects/StarForLife/team404NotFound"
    static_css_path = os.path.join(project_root, "ContestKeeper/app/static/css")
    
    for root, dirs, files in os.walk(static_css_path):
        for file in files:
            if file.endswith(".css"):
                yield os.path.join(root, file)

if __name__ == "__main__":
    for css_path in find_css_files():
        sort_css_file(css_path)
