import os
import stat
import git

def remove_readonly(func, path, excinfo):
    try:
        os.chmod(path, stat.S_IWRITE)
        func(path)
    except Exception:
        pass

def clone_repo_to_temp(repo_url: str, temp_dir: str):
    git.Repo.clone_from(repo_url, temp_dir, depth=1)
    
    target_files = []
    for root, dirs, files in os.walk(temp_dir):
        dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules', '.venv', 'build', 'dist']]
        for file in files:
            if file.endswith(('.py','.ipynb', '.js', '.ts', '.cpp', '.java', '.jsx', '.html', '.css')):
                target_files.append(os.path.join(root, file))
                
    return target_files