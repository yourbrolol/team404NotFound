import os
import re

def find_hardcoded_text(templates_dir):
    # Regex to exclude
    script_pattern = re.compile(r'<script.*?>.*?</script>', re.DOTALL | re.IGNORECASE)
    style_pattern = re.compile(r'<style.*?>.*?</style>', re.DOTALL | re.IGNORECASE)
    template_tag_pattern = re.compile(r'\{%.*?%\}', re.DOTALL)
    variable_pattern = re.compile(r'\{\{.*?\}\}', re.DOTALL)
    html_comment_pattern = re.compile(r'<!--.*?-->', re.DOTALL)
    html_tag_pattern = re.compile(r'<.*?>', re.DOTALL)
    
    findings = {}

    for root, dirs, files in os.walk(templates_dir):
        for file in files:
            if file.endswith('.html'):
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, templates_dir)
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check if it uses i18n tags at all (some files might be partially translated)
                has_i18n_load = '{% load i18n %}' in content or '{% load static i18n %}' in content
                
                # We want to find text that is NOT:
                # 1. Inside <script> or <style>
                # 2. Inside {% ... %} or {{ ... }}
                # 3. Inside HTML tags (attributes are harder to catch but we can try)
                # 4. Just whitespace or symbols
                
                # Strip out the things we want to ignore
                temp_content = script_pattern.sub('', content)
                temp_content = style_pattern.sub('', temp_content)
                temp_content = html_comment_pattern.sub('', temp_content)
                temp_content = template_tag_pattern.sub(' ', temp_content)
                temp_content = variable_pattern.sub(' ', temp_content)
                
                # Now we have HTML tags and raw text.
                # Let's find text nodes.
                # A simple way: split by tags and check parts.
                parts = re.split(r'(<.*?>)', temp_content)
                
                file_findings = []
                for part in parts:
                    if not part.startswith('<'):
                        text = part.strip()
                        # If it contains letters and isn't just symbols
                        if text and any(c.isalpha() for c in text) and len(text) > 1:
                            # Avoid common technical strings
                            if not all(c in '0123456789. ' for c in text):
                                file_findings.append(text)
                
                if file_findings:
                    findings[rel_path] = file_findings

    return findings

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    templates_path = os.path.join(base_dir, 'app', 'templates')
    
    print(f"Searching for hardcoded strings in: {templates_path}\n")
    results = find_hardcoded_text(templates_path)
    
    for file, strings in results.items():
        print(f"--- {file} ---")
        # Unique strings only for the report
        for s in sorted(list(set(strings))):
            print(f"  [ ] \"{s}\"")
        print()
