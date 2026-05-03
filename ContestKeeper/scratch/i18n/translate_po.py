#!/usr/bin/env python3
import sys
import re
import os

try:
    from deep_translator import GoogleTranslator
except ImportError:
    print("Error: 'deep-translator' is not installed.")
    print("Please run: pip install deep-translator")
    sys.exit(1)

def translate_po(po_path, mode='show'):
    if not os.path.exists(po_path):
        print(f"Error: File not found at {po_path}")
        return

    with open(po_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split into entries (separated by blank lines)
    entries = content.split('\n\n')
    new_entries = []
    to_translate = []

    for entry in entries:
        is_fuzzy = '#, fuzzy' in entry or '#|' in entry
        msgid_match = re.search(r'msgid "(.*?)"(?:\n"(.*?)")*', entry, re.DOTALL)
        msgstr_match = re.search(r'msgstr "(.*?)"(?:\n"(.*?)")*', entry, re.DOTALL)
        
        if msgid_match and msgstr_match:
            msgid = msgid_match.group(1) + (msgid_match.group(2) or "")
            msgstr = msgstr_match.group(1) + (msgstr_match.group(2) or "")
            
            # If it's untranslated OR fuzzy, we want to re-translate it
            if not msgstr or is_fuzzy:
                to_translate.append((entry, msgid))
            else:
                new_entries.append(entry)
        else:
            new_entries.append(entry)

    if not to_translate:
        print("✅ No untranslated or fuzzy entries found.")
        return

    print(f"Found {len(to_translate)} entries to fix (untranslated or fuzzy).\n")

    if mode == 'show':
        for _, msgid in to_translate:
            print(f"[ ] {msgid[:60]}...")
        return

    translator = GoogleTranslator(source='auto', target='uk')
    
    final_entries = new_entries
    for i, (original_entry, msgid) in enumerate(to_translate):
        print(f"[{i+1}/{len(to_translate)}] Fixing: {msgid[:50]}...")
        
        if not msgid.strip() or (msgid.startswith('{{') and msgid.endswith('}}')):
            final_entries.append(original_entry)
            continue

        try:
            placeholders = re.findall(r'(\{\{.*?\}\}|\{%.*?%\}|%\(.*?\)s)', msgid)
            temp_msgid = msgid
            for p_idx, p in enumerate(placeholders):
                temp_msgid = temp_msgid.replace(p, f" VZZ{p_idx} ")

            translated = translator.translate(temp_msgid)

            for p_idx, p in enumerate(placeholders):
                translated = translated.replace(f"VZZ{p_idx}", p).replace(f" VZZ{p_idx} ", p)
            
            translated = translated.replace(' }', '}').replace('{ ', '{').replace(' %', '%').replace('% ', '%')
            
            print(f"    -> {translated}")

            if mode in ['run', 'dry-run']:
                # Strip fuzzy tag while preserving the '#' prefix for other tags
                fixed_entry = original_entry
                if '#, fuzzy' in fixed_entry:
                    fixed_entry = re.sub(r'#,\s*fuzzy,?\s*', '#, ', fixed_entry)
                    fixed_entry = fixed_entry.replace('#, \n', '').replace('#, \n', '')
                    if fixed_entry.strip().endswith('#,'):
                        fixed_entry = re.sub(r'#,\s*$', '', fixed_entry.strip())

                # Replace the msgstr content
                safe_translated = translated.replace('"', '\\"')
                fixed_entry = re.sub(r'msgstr ".*?"(?:\n".*?")*', f'msgstr "{safe_translated}"', fixed_entry, flags=re.DOTALL)
                final_entries.append(fixed_entry)

        except Exception as e:
            print(f"    ❌ Error: {e}")
            final_entries.append(original_entry)

    if mode == 'run':
        with open(po_path, 'w', encoding='utf-8') as f:
            f.write('\n\n'.join(final_entries))
        print(f"\n✅ Successfully updated and cleaned {po_path}")
    elif mode == 'dry-run':
        print("\n--- DRY RUN COMPLETE ---")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 translate_po.py [show|dry-run|run]")
        sys.exit(1)

    mode = sys.argv[1].lower()
    # Path logic: assuming script is in scratch/
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    po_file = os.path.join(base_dir, 'locale', 'uk', 'LC_MESSAGES', 'django.po')
    
    translate_po(po_file, mode)
