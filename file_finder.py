"""
File finder module for the AI assistant.
This module provides functions to search for files in the system.
"""
import subprocess
import os
import re
import platform

def find_file_in_system(filename, search_path=None, file_extension=None):
    """
    Search for a file in the system using terminal commands.
    
    Args:
        filename: The name of the file to search for (can be partial)
        search_path: Optional path to limit the search to
        file_extension: Optional file extension to filter by (e.g., 'fpd', 'opd')
        
    Returns:
        The full path to the file if found, None otherwise
    """
    try:
        # Check if filename is already a full path
        if os.path.isfile(filename):
            print(f"Using provided full path: {filename}")
            return filename
            
        # Check if filename contains path separators
        if '\\' in filename or '/' in filename:
            # This might be a full path, try to use it directly
            potential_path = os.path.expanduser(filename)
            if os.path.isfile(potential_path):
                print(f"Using expanded path: {potential_path}")
                return potential_path
        
        # Clean up the filename to handle special characters
        clean_filename = re.sub(r'[^\w\s.-]', '', filename)
        
        # Determine the search paths
        search_paths = []
        
        if search_path:
            # If a specific path is provided, use it first
            search_paths.append(os.path.expanduser(search_path))
        
        # Add common locations to search
        home_dir = os.path.expanduser("~")
        desktop_dir = os.path.join(home_dir, "Desktop")
        documents_dir = os.path.join(home_dir, "Documents")
        
        # Add Desktop and its subdirectories
        if os.path.exists(desktop_dir):
            search_paths.append(desktop_dir)
            # Add "PAUT data" folder on desktop if it exists
            paut_data_dir = os.path.join(desktop_dir, "PAUT data")
            if os.path.exists(paut_data_dir):
                search_paths.append(paut_data_dir)
                # Add NaWooData subfolder if it exists
                nawoo_dir = os.path.join(paut_data_dir, "NaWooData")
                if os.path.exists(nawoo_dir):
                    search_paths.append(nawoo_dir)
        
        # Add Documents directory
        if os.path.exists(documents_dir):
            search_paths.append(documents_dir)
        
        # Add home directory as a fallback
        search_paths.append(home_dir)
        
        # Remove duplicates while preserving order
        search_paths = list(dict.fromkeys(search_paths))
        
        print(f"Searching for file: {filename}")
        print(f"Search paths: {search_paths}")
        
        # Determine the command based on the operating system
        is_windows = platform.system() == "Windows"
        
        for path in search_paths:
            print(f"Searching in: {path}")
            
            if is_windows:
                # Windows command (using PowerShell)
                if file_extension:
                    cmd = f'powershell -Command "Get-ChildItem -Path \'{path}\' -Recurse -Depth 3 -File -Filter *{clean_filename}*.{file_extension} | Select-Object -First 1 -ExpandProperty FullName"'
                else:
                    cmd = f'powershell -Command "Get-ChildItem -Path \'{path}\' -Recurse -Depth 3 -File -Filter *{clean_filename}* | Select-Object -First 1 -ExpandProperty FullName"'
            else:
                # Unix command (macOS, Linux)
                if file_extension:
                    cmd = f"find '{path}' -maxdepth 3 -type f -name '*{clean_filename}*.{file_extension}' 2>/dev/null | head -n 1"
                else:
                    cmd = f"find '{path}' -maxdepth 3 -type f -name '*{clean_filename}*' 2>/dev/null | head -n 1"
            
            print(f"Executing search command: {cmd}")
            result = subprocess.run(cmd, shell=True, text=True, capture_output=True)
            
            if result.stdout.strip():
                file_path = result.stdout.strip()
                print(f"Found file: {file_path}")
                return file_path
        
        # If we get here, we didn't find the file in any of the search paths
        print(f"No file found matching '{filename}' in any of the search paths")
        return None
            
    except Exception as e:
        print(f"Error searching for file: {e}")
        return None

def find_directory_in_system(dirname, search_path=None):
    """
    Search for a directory in the system using terminal commands.
    
    Args:
        dirname: The name of the directory to search for (can be partial)
        search_path: Optional path to limit the search to
        
    Returns:
        The full path to the directory if found, None otherwise
    """
    try:
        # Check if dirname is already a full path
        if os.path.isdir(dirname):
            print(f"Using provided full path: {dirname}")
            return dirname
            
        # Check if dirname contains path separators
        if '\\' in dirname or '/' in dirname:
            # This might be a full path, try to use it directly
            potential_path = os.path.expanduser(dirname)
            if os.path.isdir(potential_path):
                print(f"Using expanded path: {potential_path}")
                return potential_path
        
        # Clean up the dirname to handle special characters
        clean_dirname = re.sub(r'[^\w\s.-]', '', dirname)
        
        # First, check for common user directories with exact name match (case-insensitive)
        common_dirs = ["Documents", "Desktop", "Downloads", "Pictures", "Music", "Videos", "Movies", "PAUT data"]
        
        home_dir = os.path.expanduser("~")
        for common_dir in common_dirs:
            if dirname.lower() == common_dir.lower():
                common_path = os.path.join(home_dir, common_dir)
                if os.path.isdir(common_path):
                    print(f"Found common directory: {common_path}")
                    return common_path
                
                # Also check on Desktop for "PAUT data"
                if common_dir.lower() == "paut data":
                    desktop_path = os.path.join(home_dir, "Desktop", common_dir)
                    if os.path.isdir(desktop_path):
                        print(f"Found directory on Desktop: {desktop_path}")
                        return desktop_path
        
        # Check for specific paths like "Desktop/PAUT data"
        if dirname.lower() == "desktop/paut data" or dirname.lower() == "desktop\\paut data":
            desktop_paut_path = os.path.join(home_dir, "Desktop", "PAUT data")
            if os.path.isdir(desktop_paut_path):
                print(f"Found directory from path: {desktop_paut_path}")
                return desktop_paut_path
        
        # Determine the search paths
        search_paths = []
        
        if search_path:
            # If a specific path is provided, use it first
            search_paths.append(os.path.expanduser(search_path))
        
        # Add common locations to search
        search_paths.append(home_dir)
        search_paths.append(os.path.join(home_dir, "Desktop"))
        search_paths.append(os.path.join(home_dir, "Documents"))
        
        # Remove duplicates while preserving order
        search_paths = list(dict.fromkeys(search_paths))
        
        # Determine the command based on the operating system
        is_windows = platform.system() == "Windows"
        
        for path in search_paths:
            print(f"Searching for directory '{dirname}' in: {path}")
            
            if is_windows:
                # Windows command (using PowerShell)
                cmd = f'powershell -Command "Get-ChildItem -Path \'{path}\' -Directory -Recurse -Depth 2 -Filter *{clean_dirname}* | Select-Object -First 1 -ExpandProperty FullName"'
            else:
                # Unix command (macOS, Linux)
                cmd = f"find '{path}' -maxdepth 2 -type d -name '*{clean_dirname}*' 2>/dev/null | head -n 1"
            
            print(f"Executing search command: {cmd}")
            result = subprocess.run(cmd, shell=True, text=True, capture_output=True)
            
            if result.stdout.strip():
                dir_path = result.stdout.strip()
                print(f"Found directory: {dir_path}")
                return dir_path
        
        print(f"No directory found matching '{dirname}'")
        return None
            
    except Exception as e:
        print(f"Error searching for directory: {e}")
        return None

def find_files_by_extension(extension, search_path=None, limit=10):
    """
    Find files with a specific extension in the system.
    
    Args:
        extension: The file extension to search for (e.g., 'fpd', 'opd')
        search_path: Optional path to limit the search to
        limit: Maximum number of files to return
        
    Returns:
        List of file paths with the specified extension
    """
    try:
        # Determine the search path
        if not search_path:
            search_path = os.path.expanduser("~")  # Default to user's home directory
        
        # Determine the command based on the operating system
        is_windows = platform.system() == "Windows"
        
        if is_windows:
            # Windows command (using PowerShell)
            cmd = f'powershell -Command "Get-ChildItem -Path \'{search_path}\' -Recurse -Depth 3 -File -Filter *.{extension} | Select-Object -First {limit} -ExpandProperty FullName"'
        else:
            # Unix command (macOS, Linux)
            cmd = f"find '{search_path}' -maxdepth 3 -type f -name '*.{extension}' 2>/dev/null | head -n {limit}"
        
        print(f"Executing search command: {cmd}")
        result = subprocess.run(cmd, shell=True, text=True, capture_output=True)
        
        if result.stdout.strip():
            file_paths = result.stdout.strip().split('\n')
            print(f"Found {len(file_paths)} files with extension .{extension}")
            return file_paths
        else:
            print(f"No files found with extension .{extension}")
            return []
            
    except Exception as e:
        print(f"Error searching for files: {e}")
        return []

def get_most_recent_file(directory, extension=None):
    """
    Get the most recently modified file in a directory.
    
    Args:
        directory: The directory to search in
        extension: Optional file extension to filter by
        
    Returns:
        The path to the most recently modified file
    """
    try:
        if not os.path.isdir(directory):
            print(f"Directory does not exist: {directory}")
            return None
        
        # Determine the command based on the operating system
        is_windows = platform.system() == "Windows"
        
        if is_windows:
            # Windows command (using PowerShell)
            if extension:
                cmd = f'powershell -Command "Get-ChildItem -Path \'{directory}\' -File -Filter *.{extension} | Sort-Object LastWriteTime -Descending | Select-Object -First 1 -ExpandProperty FullName"'
            else:
                cmd = f'powershell -Command "Get-ChildItem -Path \'{directory}\' -File | Sort-Object LastWriteTime -Descending | Select-Object -First 1 -ExpandProperty FullName"'
        else:
            # Unix command (macOS, Linux)
            if extension:
                cmd = f"find '{directory}' -type f -name '*.{extension}' -print0 | xargs -0 ls -lt | head -n 1 | awk '{{print $NF}}'"
            else:
                cmd = f"find '{directory}' -type f -print0 | xargs -0 ls -lt | head -n 1 | awk '{{print $NF}}'"
            
        print(f"Executing command: {cmd}")
        result = subprocess.run(cmd, shell=True, text=True, capture_output=True)
        
        if result.stdout.strip():
            file_path = result.stdout.strip()
            print(f"Most recent file: {file_path}")
            return file_path
        else:
            print(f"No files found in {directory}")
            return None
            
    except Exception as e:
        print(f"Error getting most recent file: {e}")
        return None
