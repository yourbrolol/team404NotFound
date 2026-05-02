import os
import re

def smart_wrap(templates_dir, apply_changes=False):
    # Regex for attributes: attr="Text" (excluding 'value')
    attr_pattern = re.compile(r'(\s(?:placeholder|title|aria-label)=")([^"{}%]+)(")')
    
    # Regex for text nodes: >Text<
    text_node_pattern = re.compile(r'(>)([^<>{%]+)(<)')

    # Regex to identify blocks we should NEVER touch
    # 1. Django Template Tags: {% ... %}
    # 2. Django Variables: {{ ... }}
    # 3. Scripts: <script>...</script>
    # 4. Styles: <style>...</style>
    unsafe_blocks_pattern = re.compile(
        r'(\{%.*?%\}|\{\{.*?\}\}|<script.*?>.*?</script>|<style.*?>.*?</style>)', 
        re.DOTALL | re.IGNORECASE
    )

    total_changes = 0

    for root, dirs, files in os.walk(templates_dir):
        for file in files:
            if file.endswith('.html'):
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, templates_dir)
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                original_content = content
                
                # Split content into parts based on unsafe blocks
                parts = unsafe_blocks_pattern.split(content)
                
                new_parts = []
                for part in parts:
                    # If it's an unsafe block, leave it completely alone
                    if unsafe_blocks_pattern.match(part):
                        new_parts.append(part)
                        continue
                    
                    # Otherwise, process it for text nodes and attributes
                    
                    # 1. Wrap Text Nodes
                    def wrap_text_match(m):
                        prefix, text, suffix = m.groups()
                        match = re.match(r'^(\s*)(.*?)(\s*)$', text, re.DOTALL)
                        leading, content_text, trailing = match.groups()
                        
                        if content_text and any(c.isalpha() for c in content_text) and len(content_text) > 1:
                            # Heuristic: Avoid strings that look like CSS selectors or JS assignments
                            if '=' in content_text or ';' in content_text or '{' in content_text:
                                return m.group(0)
                            
                            safe_text = content_text.replace("'", "\\'")
                            return f"{prefix}{leading}{{% trans '{safe_text}' %}}{trailing}{suffix}"
                        return m.group(0)

                    # 2. Wrap Attributes
                    def wrap_attr_match(m):
                        prefix, val, suffix = m.groups()
                        safe_val = val.replace("'", "\\'")
                        return f"{prefix}{{% trans '{safe_val}' %}}{suffix}"

                    part = text_node_pattern.sub(wrap_text_match, part)
                    part = attr_pattern.sub(wrap_attr_match, part)
                    new_parts.append(part)

                content = "".join(new_parts)
                
                if content != original_content:
                    orig_lines = original_content.splitlines()
                    new_lines = content.splitlines()
                    
                    print(f"--- {rel_path} ---")
                    # Note: Line-by-line diff might look busy if tags span lines
                    for i, (orig, new) in enumerate(zip(orig_lines, new_lines)):
                        if orig != new:
                            # Only print if it's not a massive shift
                            print(f"L{i+1}:")
                            print(f"  - {orig.strip()}")
                            print(f"  + {new.strip()}")
                            total_changes += 1
                    print()

                    if apply_changes:
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(content)

    return total_changes

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    templates_path = os.path.join(base_dir, 'app', 'templates')
    
    print("--- DRY RUN: Smart i18n Wrapping (Strictly Safe) ---\n")
    changes = smart_wrap(templates_path, apply_changes=False)
    
    print(f"Total potential line changes: {changes}")
    if changes > 0:
        print("\nReview the output. If it looks correct, set 'apply_changes=True'.")
