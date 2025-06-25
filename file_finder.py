"""
File finder module for the AI assistant.
This module provides functions to search for files in the system.
"""
import subprocess
import os
import re
import platform
import glob
import sys

def find_file_in_system(filename, search_path=None, file_extension=None):
    """
    Search for a file in the system using platform-appropriate methods.
    
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
        clean_filename = filename
        
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
                # Look for NaWooData subfolder
                for item in os.listdir(paut_data_dir):
                    if "NaWooData" in item:
                        nawoo_dir = os.path.join(paut_data_dir, item)
                        if os.path.isdir(nawoo_dir):
                            search_paths.append(nawoo_dir)
                            # Also add any subfolders that might contain Korean characters
                            for subitem in os.listdir(nawoo_dir):
                                subdir = os.path.join(nawoo_dir, subitem)
                                if os.path.isdir(subdir):
                                    search_paths.append(subdir)
        
        # Add Documents directory
        if os.path.exists(documents_dir):
            search_paths.append(documents_dir)
        
        # Add home directory as a fallback
        search_paths.append(home_dir)
        
        # Remove duplicates while preserving order
        search_paths = list(dict.fromkeys(search_paths))
        
        print(f"Searching for file: {filename}")
        print(f"Search paths: {search_paths}")
        
        # Use Python's built-in glob module instead of shell commands
        for path in search_paths:
            print(f"Searching in: {path}")
            
            # Create search patterns
            if file_extension:
                search_pattern = os.path.join(path, "**", f"*{clean_filename}*.{file_extension}")
            else:
                search_pattern = os.path.join(path, "**", f"*{clean_filename}*")
            
            # Use glob with recursive search
            try:
                matches = glob.glob(search_pattern, recursive=True)
                if matches:
                    file_path = matches[0]
                    print(f"Found file: {file_path}")
                    return file_path
            except Exception as e:
                print(f"Error searching in {path}: {e}")
        
        # If we get here, we didn't find the file in any of the search paths
        print(f"No file found matching '{filename}' in any of the search paths")
        return None
            
    except Exception as e:
        print(f"Error searching for file: {e}")
        return None

def find_directory_in_system(dirname, search_path=None):
    """
    Search for a directory in the system using platform-appropriate methods.
    
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
        
        # Use Python's built-in os.walk instead of shell commands
        for path in search_paths:
            print(f"Searching for directory '{dirname}' in: {path}")
            
            for root, dirs, _ in os.walk(path):
                # Limit depth to avoid excessive searching
                if root.count(os.sep) - path.count(os.sep) > 2:
                    continue
                    
                for dir_name in dirs:
                    if dirname.lower() in dir_name.lower():
                        dir_path = os.path.join(root, dir_name)
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
        
        # Use Python's built-in glob module
        search_pattern = os.path.join(search_path, "**", f"*.{extension}")
        matches = glob.glob(search_pattern, recursive=True)
        
        if matches:
            # Limit the number of results
            limited_matches = matches[:limit]
            print(f"Found {len(limited_matches)} files with extension .{extension}")
            return limited_matches
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
        
        # Use Python's built-in functions to find the most recent file
        most_recent_file = None
        most_recent_time = 0
        
        for root, _, files in os.walk(directory):
            for file in files:
                if extension and not file.lower().endswith(f".{extension.lower()}"):
                    continue
                    
                file_path = os.path.join(root, file)
                file_time = os.path.getmtime(file_path)
                
                if file_time > most_recent_time:
                    most_recent_time = file_time
                    most_recent_file = file_path
        
        if most_recent_file:
            print(f"Most recent file: {most_recent_file}")
            return most_recent_file
        else:
            print(f"No files found in {directory}")
            return None
            
    except Exception as e:
        print(f"Error getting most recent file: {e}")
        return None
