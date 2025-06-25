"""
File finder module for the AI assistant.
This module provides functions to search for files in the system.
"""
import subprocess
import os
import re

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
        # Determine the search path
        if not search_path:
            # Default to common locations in priority order
            search_paths = [
                os.path.join(os.path.expanduser("~"), "Documents"),
                os.path.join(os.path.expanduser("~"), "Desktop"),
                os.path.join(os.path.expanduser("~"), "Downloads"),
                os.path.expanduser("~")
            ]
        else:
            search_paths = [search_path]
        
        # Search in each path until we find a match
        for path in search_paths:
            if not os.path.isdir(path):
                print(f"Skipping non-existent path: {path}")
                continue
                
            print(f"Searching in: {path}")
            
            # Build the find command
            if file_extension:
                # Search for files with specific extension
                cmd = f"find {path} -maxdepth 3 -type f -name '*{filename}*.{file_extension}' 2>/dev/null | head -n 1"
            else:
                # Search for any file containing the filename
                cmd = f"find {path} -maxdepth 3 -type f -name '*{filename}*' 2>/dev/null | head -n 1"
            
            print(f"Executing search command: {cmd}")
            result = subprocess.run(cmd, shell=True, text=True, capture_output=True)
            
            if result.stdout.strip():
                file_path = result.stdout.strip()
                print(f"Found file: {file_path}")
                return file_path
        
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
        # Determine the search path
        if not search_path:
            search_path = os.path.expanduser("~")  # Default to user's home directory
        
        # First, check for common user directories with exact name match (case-insensitive)
        common_dirs = ["Documents", "Desktop", "Downloads", "Pictures", "Music", "Videos", "Movies"]
        
        for common_dir in common_dirs:
            if dirname.lower() == common_dir.lower():
                common_path = os.path.join(os.path.expanduser("~"), common_dir)
                if os.path.isdir(common_path):
                    print(f"Found common directory: {common_path}")
                    return common_path
        
        # Next, check for direct subdirectories of home with exact name match
        home_dir = os.path.expanduser("~")
        for item in os.listdir(home_dir):
            item_path = os.path.join(home_dir, item)
            if os.path.isdir(item_path) and dirname.lower() == item.lower():
                print(f"Found exact directory match: {item_path}")
                return item_path
        
        # If no exact match, try a more limited search (only in home directory and immediate subdirectories)
        cmd = f"find {search_path} -maxdepth 2 -type d -name '*{dirname}*' 2>/dev/null | head -n 1"
        
        print(f"Executing search command: {cmd}")
        result = subprocess.run(cmd, shell=True, text=True, capture_output=True)
        
        if result.stdout.strip():
            dir_path = result.stdout.strip()
            print(f"Found directory: {dir_path}")
            return dir_path
        else:
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
        
        # Build the find command
        cmd = f"find {search_path} -type f -name '*.{extension}' 2>/dev/null | head -n {limit}"
        
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
            
        if extension:
            cmd = f"find {directory} -type f -name '*.{extension}' -print0 | xargs -0 ls -lt | head -n 1 | awk '{{print $NF}}'"
        else:
            cmd = f"find {directory} -type f -print0 | xargs -0 ls -lt | head -n 1 | awk '{{print $NF}}'"
            
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
