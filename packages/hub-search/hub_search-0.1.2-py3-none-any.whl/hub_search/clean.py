import os
import re
import sys

def run_clean(input_dir, output_file):
    # Regex for DashScope API Key
    pattern = re.compile(r"DASHSCOPE_API_KEY=(sk-[a-fA-F0-9]{32})(?![a-fA-F0-9])")
    
    found_keys = set()
    
    if not os.path.isdir(input_dir):
        print(f"Error: Directory '{input_dir}' not found.")
        sys.exit(1)

    print(f"Scanning directory: {input_dir}")
    
    for root, dirs, files in os.walk(input_dir):
        for file in files:
            file_path = os.path.join(root, file)
            
            if os.path.abspath(file_path) == os.path.abspath(output_file):
                continue

            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    matches = pattern.findall(content)
                    if matches:
                        for key in matches:
                            found_keys.add(key)
                        print(f"  Found {len(matches)} matches in {file}")
            except Exception as e:
                print(f"  [!] Error reading {file}: {e}")

    print(f"\nTotal unique keys found: {len(found_keys)}")
    
    if found_keys:
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                for key in sorted(found_keys):
                    f.write(f"{key}\n")
            print(f"Successfully wrote keys to: {output_file}")
        except Exception as e:
            print(f"Error writing output file: {e}")
    else:
        print("No matching keys found.")
