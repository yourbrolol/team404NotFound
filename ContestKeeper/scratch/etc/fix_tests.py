import os
import re

def fix_test_file(filepath):
    with open(filepath, 'r') as f:
        lines = f.readlines()

    new_lines = []
    changed = False
    
    for line in lines:
        # Check for imports of TestCase from django.test
        if 'from django.test import' in line and 'TestCase' in line:
            changed = True
            # Extract other imports if any (like Client)
            parts = line.split('import')[1].strip().split(',')
            others = [p.strip() for p in parts if p.strip() != 'TestCase' and p.strip() != 'Client']
            
            new_lines.append('from app.tests.base import BaseSecureTestCase\n')
            if others:
                new_lines.append(f'from django.test import {", ".join(others)}\n')
            continue
        
        # Replace inheritance
        if '(TestCase)' in line:
            line = line.replace('(TestCase)', '(BaseSecureTestCase)')
            changed = True
            
        # Replace Client() with self.client_class()
        if '= Client()' in line:
            line = line.replace('= Client()', '= self.client_class()')
            changed = True
            
        # Also handle cases like Client().post(...) or just Client() on its own
        # but be careful not to break imports.
        # Actually, if we've removed 'Client' from imports, it will fail if they use it.
        # So we must replace ALL instances of Client() with self.client_class()
        if 'Client()' in line and 'from' not in line:
            line = line.replace('Client()', 'self.client_class()')
            changed = True
            
        new_lines.append(line)

    if changed:
        with open(filepath, 'w') as f:
            f.writelines(new_lines)
        return True
    return False

def main():
    test_dir = 'app/tests'
    fixed_count = 0
    for root, dirs, files in os.walk(test_dir):
        for file in files:
            if file.endswith('.py') and file not in ['base.py', '__init__.py']:
                path = os.path.join(root, file)
                if fix_test_file(path):
                    fixed_count += 1
                    print(f'Fixed: {path}')
    
    print(f'Total files fixed: {fixed_count}')

if __name__ == '__main__':
    main()
