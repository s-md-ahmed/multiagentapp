def parse_repo(target_files: list) -> list:
    parsed_data = []
    MAX_LINES_PER_FILE = 200  # Enforce line limits instead of character cuts
    
    for file_path in target_files:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                lines = file.readlines()
                
            truncated = False
            if len(lines) > MAX_LINES_PER_FILE:
                lines = lines[:MAX_LINES_PER_FILE]
                truncated = True
                
            content = "".join(lines)
            if truncated:
                content += "\n# [NOTE: File truncated due to length limits. Displaying top structural lines.]\n"
                
            parsed_data.append({
                "file_path": file_path,
                "content": content
            })
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            
    return parsed_data
