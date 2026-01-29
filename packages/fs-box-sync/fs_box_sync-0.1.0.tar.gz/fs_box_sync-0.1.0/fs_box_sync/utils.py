"""Utility functions for fs-box-sync."""

import os
import re
from datetime import datetime


def format_date_folders(
    date: datetime,
    locale: str,
    year_format: str | None = None,
    month_format: str | None = None,
) -> dict[str, str]:
    """
    Format date folder names based on locale.

    Args:
        date: Date to format
        locale: Locale (e.g., 'en-US', 'ja-JP', 'zh-CN')
        year_format: Custom year format (strftime format string)
        month_format: Custom month format (strftime format string)

    Returns:
        Dictionary with 'year' and 'month' folder names

    Examples:
        >>> format_date_folders(datetime(2024, 3, 15), 'en-US')
        {'year': '2024', 'month': 'March'}

        >>> format_date_folders(datetime(2024, 3, 15), 'ja-JP')
        {'year': '2024年', 'month': '3月'}

        >>> format_date_folders(datetime(2024, 3, 15), 'en-US', '%Y', '%m')
        {'year': '2024', 'month': '03'}
    """
    # If custom formats provided, use them
    if year_format or month_format:
        return {
            "year": date.strftime(year_format or "%Y"),
            "month": date.strftime(month_format or "%-m" if os.name != "nt" else "%#m"),
        }

    # Locale-based formatting
    if locale.startswith("ja") or locale.startswith("zh"):
        return {
            "year": f"{date.year}年",
            "month": f"{date.month}月",
        }
    else:
        # English and others: 2024, March
        return {
            "year": date.strftime("%Y"),
            "month": date.strftime("%B"),
        }


def get_box_office_online_url(file_id: str, domain: str = "app.box.com") -> str:
    """
    Generate Box Office Online URL.

    Creates a URL to open files in Box Office Online (editable mode).

    Args:
        file_id: Box file ID
        domain: Box domain (e.g., 'app.box.com', 'foo.app.box.com')

    Returns:
        Office Online URL

    Example:
        >>> get_box_office_online_url('123456', 'app.box.com')
        'https://app.box.com/integrations/officeonline/openOfficeOnline?fileId=123456&sharedAccessCode='
    """
    return f"https://{domain}/integrations/officeonline/openOfficeOnline?fileId={file_id}&sharedAccessCode="


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename for safe filesystem usage.

    Removes invalid characters for Windows/Mac/Linux.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename with invalid characters replaced by underscores
    """
    # Remove invalid characters: \ / : * ? " < > |
    return re.sub(r'[\\/:*?"<>|]', "_", filename)


def get_file_extension(filename: str) -> str:
    """
    Get file extension from filename.

    Args:
        filename: Filename to extract extension from

    Returns:
        File extension without the dot, or empty string if no extension
    """
    _, ext = os.path.splitext(filename)
    return ext[1:] if ext else ""


def is_office_file(filename: str) -> bool:
    """
    Check if file is Office file type.

    Args:
        filename: Filename to check

    Returns:
        True if file has an Office extension
    """
    office_extensions = {"doc", "docx", "xls", "xlsx", "ppt", "pptx"}
    ext = get_file_extension(filename).lower()
    return ext in office_extensions
