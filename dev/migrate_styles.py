import os
import sys
import re
import hashlib

def get_class_name(style_str):
    """Generates a short, deterministic class name from style content."""
    # Clean up the style string to be a valid CSS value (minimal)
    content = style_str.lower().strip()
    h = hashlib.md5(content.encode()).hexdigest()[:6]
    return f"st-{h}"

def is_dynamic(style_str):
    """Checks if the style content contains Django template logic."""
    return "{{" in style_str or "{%" in style_str

def find_css_file(html_path):
    """Finds the corresponding CSS file in static/css."""
    base_name = os.path.basename(html_path)
    css_name = os.path.splitext(base_name)[0] + ".css"
    
    project_root = "/mnt/data/Documents/Projects/StarForLife/team404NotFound"
    static_css_path = os.path.join(project_root, "ContestKeeper/app/static/css")
    
    for root, dirs, files in os.walk(static_css_path):
        if css_name in files:
            return os.path.join(root, css_name)
    return None

def migrate_styles(html_path):
    print(f"Processing: {html_path}")
    
    css_path = find_css_file(html_path)
    if not css_path:
        print(f"  Skipping: No corresponding CSS file found for {html_path}")
        return

    with open(html_path, 'r') as f:
        content = f.read()

    # Map to store styles for the CSS file
    extracted_styles = {}
    
    def tag_migrator(match):
        tag_name = match.group(1)
        attributes = match.group(2)
        
        # Check for style attribute
        style_match = re.search(r'style="([^"]*)"', attributes)
        if not style_match:
            return match.group(0)
            
        style_content = style_match.group(1).strip()
        if not style_content or is_dynamic(style_content):
            return match.group(0)
            
        cls = get_class_name(style_content)
        extracted_styles[cls] = style_content
        
        # Remove style attribute from attributes string
        # We use replace with the exact string found
        new_attrs = attributes.replace(style_match.group(0), "")
        
        # Add to or create class attribute
        class_match = re.search(r'class="([^"]*)"', new_attrs)
        if class_match:
            existing_classes = class_match.group(1)
            if cls not in existing_classes.split():
                updated_class_attr = f'class="{existing_classes} {cls}"'
            else:
                updated_class_attr = f'class="{existing_classes}"'
            new_attrs = new_attrs.replace(class_match.group(0), updated_class_attr)
        else:
            new_attrs = f'{new_attrs.strip()} class="{cls}"'
            
        # Clean up whitespace
        new_attrs = re.sub(r'\s+', ' ', new_attrs).strip()
        if new_attrs:
            return f'<{tag_name} {new_attrs}>'
        else:
            return f'<{tag_name}>'

    # Match any <tag ...> where style="..." exists
    # We use a broad match for tags
    tag_pattern = re.compile(r'<([a-zA-Z0-9]+)([^>]*)>')
    new_content = tag_pattern.sub(tag_migrator, content)
    
    if not extracted_styles:
        print(f"  No static styles to move.")
        return
    
    # Pass 3: Ensure the CSS file is linked in the template
    # We look for static/css/... matching the file name
    project_root = "/mnt/data/Documents/Projects/StarForLife/team404NotFound"
    rel_css_path = os.path.relpath(css_path, os.path.join(project_root, "ContestKeeper/app/static"))
    link_tag = f'<link rel="stylesheet" href="{{% static \'{rel_css_path}\' %}}">'
    
    if rel_css_path not in new_content:
        # Try to find a good place to insert the link
        if "{% block extra_css %}" in new_content:
            new_content = new_content.replace("{% block extra_css %}", f"{{% block extra_css %}}\n{link_tag}")
        elif "{% extends" in new_content:
            # Insert after the extend/load static block if extra_css doesn't exist
            link_block = f"\n{{% block extra_css %}}\n{link_tag}\n{{% endblock %}}\n"
            if "{% load static %}" in new_content:
                new_content = new_content.replace("{% load static %}", f"{{% load static %}}\n{link_block}")
            else:
                match = re.search(r'{% extends [^%]+ %}', new_content)
                if match:
                    new_content = new_content.replace(match.group(0), f"{match.group(0)}\n{{% load static %}}\n{link_block}")
    
    # Save the updated HTML
    with open(html_path, 'w') as f:
        f.write(new_content)
        
    # Append the rules to the CSS file
    # We check if they already exist to avoid bloating if script is run multiple times
    with open(css_path, 'r') as f:
        existing_css = f.read()
        
    with open(css_path, 'a') as f:
        f.write(f"\n/* --- Extracted from {os.path.basename(html_path)} --- */\n")
        for cls, rules in extracted_styles.items():
            if f".{cls}" not in existing_css:
                f.write(f".{cls} {{ {rules} }}\n")
            
    print(f"  Success: Extracted {len(extracted_styles)} styles to {os.path.basename(css_path)}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python migrate_styles.py <html_file1> [html_file2 ...]")
        sys.exit(1)
    
    for path in sys.argv[1:]:
        migrate_styles(path)
