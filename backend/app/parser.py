def parse_repo(target_files: list) -> list:
    MAX_LINES_PER_FILE = 200  # Enforce line limits instead of character cuts
    
    # Sort files to prioritize backend logic first, then frontend JS, then HTML templates
    def file_priority(path: str) -> int:
        path_lower = path.lower()
        if path_lower.endswith(('.py', '.js', '.ts')) and not 'frontend' in path_lower and not 'static' in path_lower:
            return 1  # Core backend code first
        elif path_lower.endswith(('.js', '.jsx')) and ('frontend' in path_lower or 'static' in path_lower):
            return 2  # Frontend JS logic second
        elif path_lower.endswith('.html'):
            return 3  # HTML structure third
        else:
            return 4  # Everything else last

    sorted_files = sorted(target_files, key=file_priority)
    parsed_data = []
    
    for file_path in sorted_files:
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
