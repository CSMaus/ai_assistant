"""
Enhanced file finder module for the AI assistant.
This module provides functions to search for files in the system with improved fuzzy matching.
"""
import os
import re
import glob
import platform
import difflib
from typing import List, Optional, Tuple

def normalize_filename(filename: str) -> str:
    """
    Normalize a filename for fuzzy matching by:
    - Converting to lowercase
    - Removing special characters
    - Replacing spaces, dashes, underscores with wildcards
    
    Args:
        filename: The filename to normalize
        
    Returns:
        Normalized filename for matching
    """
    # Convert to lowercase
    normalized = filename.lower()
    
    # Replace spaces, dashes, underscores with a regex pattern that matches any of them
    normalized = re.sub(r'[-_\s]+', '[-_\\s]*', normalized)
    
    # Remove file extension if present
    normalized = re.sub(r'\.(opd|fpd)$', '', normalized)
    
    return normalized

def generate_alternative_patterns(filename: str) -> List[str]:
    """
    Generate alternative patterns for a filename to handle missing spaces and special characters.
    
    Args:
        filename: The filename to generate alternatives for
        
    Returns:
        List of alternative patterns
    """
    alternatives = []
    
    # Original filename
    alternatives.append(filename)
    
    # Remove all spaces, dashes, underscores
    no_special = re.sub(r'[-_\s]+', '', filename)
    alternatives.append(no_special)
    
    # Extract just the numbers
    numbers_only = ''.join(re.findall(r'\d+', filename))
    if numbers_only:
        alternatives.append(numbers_only)
    
    # Extract letter-number combinations (e.g., "D25" from "D25-28")
    letter_number_patterns = re.findall(r'[a-zA-Z]\d+', filename)
    if letter_number_patterns:
        alternatives.extend(letter_number_patterns)
    
    # Handle common number ranges (e.g., "25-28" -> "25", "28")
    range_patterns = re.findall(r'(\d+)[-_\s]+(\d+)', filename)
    for start, end in range_patterns:
        alternatives.append(start)
        alternatives.append(end)
        alternatives.append(start + end)  # e.g., "2528"
    
    return list(set(alternatives))  # Remove duplicates

def score_filename_match(query: str, filename: str) -> float:
    """
    Score how well a filename matches a query.
    
    Args:
        query: The search query
        filename: The filename to match against
        
    Returns:
        Score between 0 and 1, higher is better match
    """
    # Get just the basename without path
    basename = os.path.basename(filename)
    
    # Convert both to lowercase for case-insensitive matching
    query_lower = query.lower()
    basename_lower = basename.lower()
    
    # Generate alternative patterns for the query
    query_alternatives = generate_alternative_patterns(query_lower)
    basename_alternatives = generate_alternative_patterns(basename_lower)
    
    # Calculate scores for each alternative
    scores = []
    
    # Basic sequence matcher score
    basic_score = difflib.SequenceMatcher(None, query_lower, basename_lower).ratio()
    scores.append(basic_score)
    
    # Check if any alternative of the query is contained in any alternative of the basename
    for q_alt in query_alternatives:
        for b_alt in basename_alternatives:
            if q_alt in b_alt or b_alt in q_alt:
                # Calculate how much of one is contained in the other
                containment_score = len(q_alt) / max(len(b_alt), 1) if len(q_alt) < len(b_alt) else len(b_alt) / max(len(q_alt), 1)
                scores.append(0.7 + (containment_score * 0.3))  # Base score of 0.7 plus containment factor
    
    # Check for exact number matches (e.g., "25" in "D25-28_01.opd")
    query_numbers = re.findall(r'\d+', query_lower)
    basename_numbers = re.findall(r'\d+', basename_lower)
    
    if query_numbers and basename_numbers:
        matching_numbers = sum(1 for qn in query_numbers if any(qn in bn for bn in basename_numbers))
        if matching_numbers > 0:
            number_match_score = matching_numbers / len(query_numbers)
            scores.append(0.6 + (number_match_score * 0.4))  # Base score of 0.6 plus number match factor
    
    # Check for consecutive digits (e.g., "252801" matching "D25-28_01.opd")
    query_digits = ''.join(re.findall(r'\d', query_lower))
    basename_digits = ''.join(re.findall(r'\d', basename_lower))
    
    if query_digits and basename_digits:
        if query_digits in basename_digits or basename_digits in query_digits:
            digit_match_score = len(query_digits) / max(len(basename_digits), 1) if len(query_digits) < len(basename_digits) else len(basename_digits) / max(len(query_digits), 1)
            scores.append(0.8 + (digit_match_score * 0.2))  # High base score of 0.8 for digit matches
    
    # Return the highest score
    return max(scores) if scores else 0.0

def find_file_in_system(filename: str, search_path: Optional[str] = None, file_extension: Optional[str] = None) -> Optional[str]:
    """
    Search for a file in the system using fuzzy matching.
    
    Args:
        filename: The name of the file to search for (can be partial)
        search_path: Optional path to limit the search to
        file_extension: Optional file extension to filter by (e.g., 'fpd', 'opd')
        
    Returns:
        The full path to the best matching file if found, None otherwise
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
        
        # Generate alternative search patterns
        search_alternatives = generate_alternative_patterns(filename)
        print(f"Search alternatives: {search_alternatives}")
        
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
                # Look for NaWooData subfolder and other subfolders
                for item in os.listdir(paut_data_dir):
                    item_path = os.path.join(paut_data_dir, item)
                    if os.path.isdir(item_path):
                        search_paths.append(item_path)
                        # Also add any subfolders that might contain data files
                        try:
                            for subitem in os.listdir(item_path):
                                subdir = os.path.join(item_path, subitem)
                                if os.path.isdir(subdir):
                                    search_paths.append(subdir)
                        except Exception as e:
                            print(f"Error accessing directory {item_path}: {e}")
        
        # Add Documents directory
        if os.path.exists(documents_dir):
            search_paths.append(documents_dir)
        
        # Add home directory as a fallback
        search_paths.append(home_dir)
        
        # Remove duplicates while preserving order
        search_paths = list(dict.fromkeys(search_paths))
        
        print(f"Searching for file: {filename}")
        print(f"Search paths: {search_paths}")
        
        # Collect all potential matches with their scores
        matches = []
        
        for path in search_paths:
            print(f"Searching in: {path}")
            
            # Create search patterns
            extensions = [file_extension] if file_extension else ["opd", "fpd"]
            
            for ext in extensions:
                # Use recursive glob to find all files with the extension
                pattern = os.path.join(path, "**", f"*.{ext}")
                try:
                    for file_path in glob.glob(pattern, recursive=True):
                        # Score the match
                        score = score_filename_match(filename, file_path)
                        if score > 0.3:  # Only consider reasonable matches
                            matches.append((file_path, score))
                except Exception as e:
                    print(f"Error searching in {path} for .{ext} files: {e}")
        
        # Sort matches by score (highest first)
        matches.sort(key=lambda x: x[1], reverse=True)
        
        # Print top matches for debugging
        print(f"Found {len(matches)} potential matches")
        for i, (path, score) in enumerate(matches[:5]):
            print(f"Match {i+1}: {os.path.basename(path)} (score: {score:.2f}) - {path}")
        
        # Return the best match if any
        if matches:
            best_match = matches[0][0]
            print(f"Best match: {best_match}")
            return best_match
        
        print(f"No file found matching '{filename}' in any of the search paths")
        return None
            
    except Exception as e:
        print(f"Error searching for file: {e}")
        import traceback
        traceback.print_exc()
        return None

def find_directory_in_system(dirname: str, search_path: Optional[str] = None) -> Optional[str]:
    """
    Search for a directory in the system using fuzzy matching.
    
    Args:
        dirname: The name of the directory to search for (can be partial)
        search_path: Optional path to limit the search to
        
    Returns:
        The full path to the best matching directory if found, None otherwise
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
        
        # Normalize the dirname for better matching
        normalized_dirname = normalize_filename(dirname)
        
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
        
        # Collect all potential matches with their scores
        matches = []
        
        for path in search_paths:
            print(f"Searching for directory '{dirname}' in: {path}")
            
            try:
                for root, dirs, _ in os.walk(path):
                    # Limit depth to avoid excessive searching
                    if root.count(os.sep) - path.count(os.sep) > 2:
                        continue
                        
                    for dir_name in dirs:
                        # Score the match
                        score = score_filename_match(dirname, dir_name)
                        if score > 0.3:  # Only consider reasonable matches
                            dir_path = os.path.join(root, dir_name)
                            matches.append((dir_path, score))
            except Exception as e:
                print(f"Error searching in {path}: {e}")
        
        # Sort matches by score (highest first)
        matches.sort(key=lambda x: x[1], reverse=True)
        
        # Print top matches for debugging
        print(f"Found {len(matches)} potential directory matches")
        for i, (path, score) in enumerate(matches[:5]):
            print(f"Match {i+1}: {os.path.basename(path)} (score: {score:.2f}) - {path}")
        
        # Return the best match if any
        if matches:
            best_match = matches[0][0]
            print(f"Best directory match: {best_match}")
            return best_match
        
        print(f"No directory found matching '{dirname}'")
        return None
            
    except Exception as e:
        print(f"Error searching for directory: {e}")
        import traceback
        traceback.print_exc()
        return None

def find_files_by_extension(extension: str, search_path: Optional[str] = None, limit: int = 10) -> List[str]:
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

def get_most_recent_file(directory: str, extension: Optional[str] = None) -> Optional[str]:
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
