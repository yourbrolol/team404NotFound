import os
import sys
import re
from collections import defaultdict

def rename_classes_in_pair(html_path, css_path):
    if not os.path.exists(html_path) or not os.path.exists(css_path):
        return

    print(f"Renaming classes in: {os.path.basename(html_path)}")

    with open(html_path, 'r') as f:
        html_content = f.read()
    
    with open(css_path, 'r') as f:
        css_content = f.read()

    # Find all st-xxxxxx classes in the HTML
    # We look for them specifically in class="..." attributes or in the CSS
    # Let's find all unique st-hash patterns
    st_classes = sorted(list(set(re.findall(r'st-[a-f0-9]{6}', html_content))))
    
    if not st_classes:
        print(f"  No 'st-' classes found in {html_path}")
        return

    mapping = {}
    counters = defaultdict(int)
    
    for old_cls in st_classes:
        # Find the tag(s) associated with this class in HTML
        # We look for <tag ... class="... st-hash ..." ...>
        # This regex looks for the tag name preceding the class
        tag_match = re.search(r'<([a-zA-Z0-9]+)[^>]+class="[^"]*?\b' + old_cls + r'\b[^"]*"', html_content)
        
        if tag_match:
            tag_name = tag_match.group(1).lower()
        else:
            tag_name = "style" # Fallback
            
        counters[tag_name] += 1
        new_cls = f"{tag_name}-{counters[tag_name]:03d}"
        mapping[old_cls] = new_cls

    # Perform replacements
    # Important: use word boundaries to avoid partial matches
    updated_html = html_content
    updated_css = css_content
    
    for old, new in mapping.items():
        # Replace in HTML (attributes)
        updated_html = re.sub(r'\b' + old + r'\b', new, updated_html)
        # Replace in CSS (selectors)
        updated_css = re.sub(r'\.' + old + r'\b', '.' + new, updated_css)

    with open(html_path, 'w') as f:
        f.write(updated_html)
    
    with open(css_path, 'w') as f:
        f.write(updated_css)

    print(f"  Success: Renamed {len(mapping)} classes (e.g., {list(mapping.values())[0]})")

def find_pairs():
    """Finds all HTML files and their corresponding CSS files using the project structure."""
    project_root = "/mnt/data/Documents/Projects/StarForLife/team404NotFound"
    templates_root = os.path.join(project_root, "ContestKeeper/app/templates")
    static_css_path = os.path.join(project_root, "ContestKeeper/app/static/css")
    
    for root, dirs, files in os.walk(templates_root):
        for file in files:
            if file.endswith(".html"):
                html_path = os.path.join(root, file)
                # Try to find corresponding CSS
                css_name = os.path.splitext(file)[0] + ".css"
                found_css = None
                for c_root, c_dirs, c_files in os.walk(static_css_path):
                    if css_name in c_files:
                        found_css = os.path.join(c_root, css_name)
                        break
                
                if found_css:
                    yield html_path, found_css

if __name__ == "__main__":
    pairs = list(find_pairs())
    for html, css in pairs:
        rename_classes_in_pair(html, css)
