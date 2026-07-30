"""
File Validation Utilities
==========================
Implements comprehensive file upload validation including:
- MIME type validation
- File extension validation
- Magic bytes (file signature) validation
- File size validation
"""

import os
import struct
from typing import Tuple, Optional
from fastapi import HTTPException


# Magic bytes signatures for common image formats
MAGIC_BYTES = {
    # JPEG
    b'\xff\xd8\xff': ('image/jpeg', '.jpg', '.jpeg'),
    # PNG
    b'\x89\x50\x4e\x47': ('image/png', '.png'),
    # WebP
    b'\x52\x49\x46\x46': ('image/webp', '.webp'),  # RIFF header
    # GIF
    b'\x47\x49\x46\x38': ('image/gif', '.gif'),
    # BMP
    b'\x42\x4d': ('image/bmp', '.bmp'),
}


# Allowed MIME types and their extensions
ALLOWED_TYPES = {
    'image/jpeg': ['.jpg', '.jpeg'],
    'image/jpg': ['.jpg', '.jpeg'],
    'image/png': ['.png'],
    'image/webp': ['.webp'],
    'image/gif': ['.gif'],
    'image/bmp': ['.bmp'],
}


def get_file_magic_bytes(file_path: str, max_bytes: int = 12) -> bytes:
    """
    Read the first N bytes of a file to determine its type.
    
    Args:
        file_path: Path to the file
        max_bytes: Number of bytes to read (default: 12)
        
    Returns:
        First N bytes of the file
    """
    try:
        with open(file_path, 'rb') as f:
            return f.read(max_bytes)
    except Exception:
        return b''


def detect_file_type(file_path: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Detect file type using magic bytes.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Tuple of (mime_type, extension) or (None, None) if unknown
    """
    magic = get_file_magic_bytes(file_path)
    
    for signature, (mime_type, *extensions) in MAGIC_BYTES.items():
        if magic.startswith(signature):
            return mime_type, extensions[0] if extensions else None
    
    return None, None


def validate_file_extension(filename: str, allowed_mime_types: list) -> bool:
    """
    Validate file extension against allowed MIME types.
    
    Args:
        filename: Name of the file
        allowed_mime_types: List of allowed MIME types
        
    Returns:
        True if extension is valid, False otherwise
    """
    if not filename or '.' not in filename:
        return False
    
    ext = os.path.splitext(filename)[1].lower()
    
    for mime_type in allowed_mime_types:
        if ext in ALLOWED_TYPES.get(mime_type, []):
            return True
    
    return False


def validate_mime_type(declared_mime: str, detected_mime: Optional[str]) -> bool:
    """
    Validate that declared MIME type matches detected type.
    
    Args:
        declared_mime: MIME type declared by client
        detected_mime: MIME type detected from magic bytes
        
    Returns:
        True if types match or detected is None, False otherwise
    """
    if detected_mime is None:
        # If we can't detect, allow but log warning
        return True
    
    # Normalize MIME types (image/jpg -> image/jpeg)
    declared_normalized = declared_mime.lower().replace('image/jpg', 'image/jpeg')
    detected_normalized = detected_mime.lower().replace('image/jpg', 'image/jpeg')
    
    return declared_normalized == detected_normalized


def validate_file_size(file_size: int, max_size: int) -> bool:
    """
    Validate file size against maximum allowed size.
    
    Args:
        file_size: Size of the file in bytes
        max_size: Maximum allowed size in bytes
        
    Returns:
        True if size is valid, False otherwise
    """
    return file_size <= max_size


def validate_file_upload(
    filename: str,
    content_type: str,
    file_size: int,
    file_path: str,
    allowed_mime_types: list,
    max_file_size: int
) -> Tuple[bool, Optional[str]]:
    """
    Comprehensive file upload validation.
    
    Args:
        filename: Name of the uploaded file
        content_type: Declared MIME type
        file_size: Size of the file in bytes
        file_path: Temporary path to the file
        allowed_mime_types: List of allowed MIME types
        max_file_size: Maximum allowed file size in bytes
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Validate file size
    if not validate_file_size(file_size, max_file_size):
        max_mb = max_file_size / (1024 * 1024)
        return False, f"File too large. Maximum size is {max_mb:.1f}MB"
    
    # Validate file extension
    if not validate_file_extension(filename, allowed_mime_types):
        return False, f"Invalid file extension. Allowed types: {', '.join(allowed_mime_types)}"
    
    # Validate MIME type is allowed
    if content_type.lower() not in [m.lower() for m in allowed_mime_types]:
        return False, f"Invalid file type. Allowed types: {', '.join(allowed_mime_types)}"
    
    # Detect actual file type from magic bytes
    detected_mime, detected_ext = detect_file_type(file_path)
    
    if detected_mime is None:
        # Unknown file type - reject
        return False, "Unable to determine file type. File may be corrupted or unsupported."
    
    # Validate declared MIME type matches detected type
    if not validate_mime_type(content_type, detected_mime):
        return False, f"File type mismatch. Declared: {content_type}, Detected: {detected_mime}"
    
    # Validate detected MIME type is allowed
    if detected_mime.lower() not in [m.lower() for m in allowed_mime_types]:
        return False, f"Detected file type not allowed: {detected_mime}"
    
    # Validate file extension matches detected type
    if detected_ext:
        file_ext = os.path.splitext(filename)[1].lower()
        if file_ext != detected_ext and file_ext not in ALLOWED_TYPES.get(detected_mime, []):
            return False, f"File extension does not match file content. Extension: {file_ext}, Detected: {detected_ext}"
    
    return True, None


def validate_safe_file(file_path: str) -> bool:
    """
    Additional safety checks to ensure file is not executable or malicious.
    
    Args:
        file_path: Path to the file
        
    Returns:
        True if file is safe, False otherwise
    """
    try:
        # Check for executable signatures
        magic = get_file_magic_bytes(file_path, max_bytes=4)
        
        # Reject executable signatures
        dangerous_signatures = [
            b'MZ',  # Windows executable
            b'\x7fELF',  # Linux executable
            b'CAFE',  # Java class
            b'PK\x03\x04',  # ZIP (could contain executables)
        ]
        
        for sig in dangerous_signatures:
            if magic.startswith(sig):
                return False
        
        # Check file size (reject empty files)
        file_size = os.path.getsize(file_path)
        if file_size == 0:
            return False
        
        return True
        
    except Exception:
        return False
