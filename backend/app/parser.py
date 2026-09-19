def parse_repo(target_files: list) -> list:
    parsed_data = []
    MAX_CHARS_PER_FILE = 6000  # Tighter cap so single files don't hog the whole budget
    
    for file_path in target_files:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                content = file.read()
                
                if len(content) > MAX_CHARS_PER_FILE:
                    content = content[:MAX_CHARS_PER_FILE]
                
                parsed_data.append({
                    "file_path": file_path,
                    "content": content
                })
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            
    return parsed_data