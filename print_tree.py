import os

def print_directory_tree(startpath, exclude_dirs=None):
    if exclude_dirs is None:
        exclude_dirs = {'.git', '__pycache__', '.idea', 'venv'}

    for root, dirs, files in os.walk(startpath):
        # Remove excluded directories
        dirs[:] = [d for d in dirs if d not in exclude_dirs]

        level = root.replace(startpath, '').count(os.sep)
        indent = '│   ' * (level)
        print(f'{indent}├── {os.path.basename(root)}/')
        subindent = '│   ' * (level + 1)
        for f in files:
            print(f'{subindent}├── {f}')


if __name__ == "__main__":
    # Get the current working directory
    current_dir = os.getcwd()
    print(f"\nDirectory tree starting from: {current_dir}\n")
    print_directory_tree(current_dir)