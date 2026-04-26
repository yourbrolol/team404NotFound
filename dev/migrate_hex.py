import os
import re

# Comprehensive dictionary based on our previous mapping (since the block in common.css was deleted)
COLOR_MAPPING = {
    # Primary & Brands -> var(--primary)
    '#6366f1': 'var(--primary)',
    '#667eea': 'var(--primary)',
    '#5865f2': 'var(--primary)',
    '#818cf8': 'var(--bg-primary-tint)', # light
    '#eef2ff': 'var(--bg-primary-tint)', # lightest
    '#1e1b4b': 'var(--primary-hover)',   # dark

    # Success & Greens -> var(--success)
    '#10b981': 'var(--success)',
    '#2ecc71': 'var(--success)',
    '#4ade80': 'var(--success)',
    '#28a745': 'var(--success)',
    '#d1fae5': 'var(--bg-success-tint)', # light
    '#065f46': 'var(--success)',         # dark

    # Error & Reds -> var(--error)
    '#ef4444': 'var(--error)',
    '#e74c3c': 'var(--error)',
    '#f87171': 'var(--error)',
    '#e53e3e': 'var(--error)',
    '#dc3545': 'var(--error)',
    '#ff0000': 'var(--error)',
    '#fee2e2': 'var(--bg-error-tint)',   # light
    '#ffcccc': 'var(--bg-error-tint)',   # lightest
    '#991b1b': 'var(--error)',           # dark

    # Warnings & Info
    '#f59e0b': 'var(--warning)',
    '#ffc107': 'var(--warning)',
    '#17a2b8': 'var(--info)',
    '#0088cc': 'var(--info)',
    '#3498db': 'var(--info)',

    # Dark Background Slates -> var(--bg-dark) / var(--bg-card-hover)
    '#111827': 'var(--bg-dark)',
    '#24292e': 'var(--bg-dark)',
    '#1f2937': 'var(--bg-dark)',
    '#1e293b': 'var(--bg-card-hover)',
    '#0f172a': 'var(--bg-dark)',

    # Grays & Muted -> var(--text-muted)
    '#6b7280': 'var(--text-muted)',
    '#6c757d': 'var(--text-muted)',
    '#a1a1aa': 'var(--text-muted)',
    '#475569': 'var(--text-muted)',
    '#374151': 'var(--text-muted)',
    '#4b5563': 'var(--text-muted)',

    # Light & Whites -> text-main, input-text, border
    '#ffffff': 'var(--input-text)',
    '#fff':    'var(--input-text)',
    '#f8fafc': 'var(--text-main)',
    '#f5f7fa': 'var(--text-main)',
    '#c3cfe2': 'var(--border)',
    '#e2e8f0': 'var(--border)',
}

EXCLUDE_DIRS = {'.git', 'node_modules', '.venv', '.lvenv'}
EXCLUDE_FILES = {'common.css'} 

def migrate_hex():
    total_swapped = 0
    not_found = set()
    file_count = 0
    
    print("\nStarting Hex Color Migration to CSS Variables...")
    print("-" * 60)

    for root, dirs, files in os.walk('.'):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        
        for file in files:
            if file in EXCLUDE_FILES:
                continue
            
            # Target CSS files
            if not file.endswith('.css'):
                 continue
                
            path = os.path.join(root, file)
            
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except Exception:
                continue

            # Find all hex colors in this file
            hex_matches = re.findall(r'#[0-9a-fA-F]{3,8}(?![0-9a-fA-F])', content)
            if not hex_matches:
                continue
                
            new_content = content
            replacements_in_file = 0

            # Sort by length descending to prevent partial replace like replacing #fff inside #ffffff
            unique_hexes = sorted(set(hex_matches), key=len, reverse=True)
            
            for hx in unique_hexes:
                hx_lower = hx.lower()
                
                if hx_lower in COLOR_MAPPING:
                    var_replace = COLOR_MAPPING[hx_lower]
                    
                    # Regex to replace case-insensitive but ensuring no partial trailing chars
                    pattern = re.compile(re.escape(hx) + r'(?![0-9a-fA-F])', re.IGNORECASE)
                    
                    count = len(pattern.findall(new_content))
                    if count > 0:
                        new_content = pattern.sub(var_replace, new_content)
                        replacements_in_file += count
                        total_swapped += count
                else:
                    # Log any hex that isn't mapped
                    not_found.add(hx_lower)

            if replacements_in_file > 0:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"[{replacements_in_file:>2} swapped] {path}")
                file_count += 1

    print("-" * 60)
    print(f"Total Replacements: {total_swapped}")
    print(f"Files Modified:    {file_count}\n")
    
    if not_found:
        print("Hex Colors Not Found in Mapping (Skipped):")
        for nf in sorted(not_found):
            print(f"  - {nf}")
    else:
        print("All discovered hex colors were successfully mapped!")

if __name__ == "__main__":
    migrate_hex()
