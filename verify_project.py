import os
import sys
import importlib.util

# Ensure stdout handles emojis and utf-8
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def check_file(file_path):
    print(f"Checking {file_path}...")
    try:
        # Check syntax
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        compile(source, file_path, 'exec')
        
        # Try to import only utils for now, as pages might depend on streamlit context
        if "utils" in file_path and not file_path.endswith("__init__.py"):
            module_name = file_path.replace(".\\", "").replace("\\", ".").replace(".py", "")
            if module_name.startswith("."): module_name = module_name[1:]
            print(f"  Attempting to import {module_name}...")
            # We use importlib to avoid polluting the namespace too much
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
        
        return True, None
    except Exception as e:
        return False, str(e)

def main():
    root_dir = "."
    files_to_check = []
    
    # Root files
    for f in os.listdir(root_dir):
        if f.endswith(".py"):
            files_to_check.append(os.path.join(root_dir, f))
            
    # Subdirectories
    for sub in ["pages", "utils"]:
        sub_dir = os.path.join(root_dir, sub)
        if os.path.exists(sub_dir):
            for f in os.listdir(sub_dir):
                if f.endswith(".py"):
                    files_to_check.append(os.path.join(sub_dir, f))
                    
    results = []
    for f in files_to_check:
        success, error = check_file(f)
        if not success:
            results.append((f, error))
            
    if not results:
        print("✅ No syntax errors found.")
    else:
        print(f"❌ Found {len(results)} errors:")
        for f, err in results:
            print(f"--- {f} ---\n{err}\n")

if __name__ == "__main__":
    main()
