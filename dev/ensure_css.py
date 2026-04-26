import os
import sys

def find_css_recursively(css_name, search_path):
    """Checks if css_name exists anywhere inside search_path."""
    for root, dirs, files in os.walk(search_path):
        if css_name in files:
            return os.path.join(root, css_name)
    return None

def ensure_css(html_path):
    # Standardize path
    html_path = os.path.abspath(html_path)
    base_name = os.path.basename(html_path)
    css_name = os.path.splitext(base_name)[0] + ".css"
    
    # Define the base static CSS path relative to the project structure
    # Based on our exploration: ContestKeeper/app/static/css/
    # We'll assume the script is run from the project root.
    project_root = "/mnt/data/Documents/Projects/StarForLife/team404NotFound"
    static_css_path = os.path.join(project_root, "ContestKeeper/app/static/css")
    
    if not os.path.exists(static_css_path):
        print(f"Error: Static CSS path {static_css_path} does not exist.")
        return

    found_path = find_css_recursively(css_name, static_css_path)
    
    if found_path:
        print(f"EXISTS: {os.path.relpath(found_path, project_root)}")
        return found_path
    else:
        # Logic to determine where to create the NEW css file.
        # We try to mirror the directory structure under templates/app/
        # e.g. .../templates/app/admin/analytics.html -> .../static/css/admin/analytics.css
        
        target_dir = static_css_path
        
        try:
            # Detect subdirectories under templates
            if "templates" in html_path:
                parts = html_path.split(os.sep)
                t_idx = parts.index("templates")
                # Structure is usually templates/app/folder/file.html
                # We want folder/file.css
                sub_path_parts = parts[t_idx+1:]
                
                # Skip 'app' or app name if it's the first child of templates
                if len(sub_path_parts) > 1 and sub_path_parts[0] == "app":
                    sub_path_parts = sub_path_parts[1:]
                
                if len(sub_path_parts) > 1:
                    sub_dir = os.path.join(*sub_path_parts[:-1])
                    target_dir = os.path.join(static_css_path, sub_dir)
            
            os.makedirs(target_dir, exist_ok=True)
            target_file = os.path.join(target_dir, css_name)
            
            with open(target_file, "w") as f:
                f.write(f"/* Styles for {base_name} */\n")
            
            print(f"CREATED: {os.path.relpath(target_file, project_root)}")
            return target_file
            
        except Exception as e:
            print(f"Error creating CSS for {base_name}: {e}")
            return None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python ensure_css.py <path_to_html_file>")
        sys.exit(1)
    
    for arg in sys.argv[1:]:
        ensure_css(arg)
