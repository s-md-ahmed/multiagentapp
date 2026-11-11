# parser.py
import os
import logging

logger = logging.getLogger(__name__)

def parse_repo(target_files: list, base_temp_dir: str = None) -> list:
    MAX_LINES_PER_FILE = 200  
    
    def file_priority(path: str) -> int:
        path_lower = path.lower()
        if path_lower.endswith(('.py', '.js', '.ts')) and not 'frontend' in path_lower and not 'static' in path_lower:
            return 1  
        elif path_lower.endswith(('.js', '.jsx')) and ('frontend' in path_lower or 'static' in path_lower):
            return 2  
        elif path_lower.endswith('.html'):
            return 3  
        else:
            return 4  

    sorted_files = sorted(target_files, key=file_priority)
    parsed_data = []
    
    abs_base_dir = os.path.abspath(base_temp_dir) if base_temp_dir else None

    for file_path in sorted_files:
        try:
            abs_file_path = os.path.abspath(file_path)
            # Security guard: prevent path traversal / arbitrary file read outside temp dir
            if abs_base_dir and not abs_file_path.startswith(abs_base_dir):
                logger.warning(f"Skipping path traversal attempt: {file_path}")
                continue

            with open(abs_file_path, 'r', encoding='utf-8', errors='ignore') as file:
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
            # Replaced raw print with proper structured logger warning
            logger.error(f"Error reading {file_path}: {e}")
            
    return parsed_data
