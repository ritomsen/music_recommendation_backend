from fastapi import UploadFile
import aiofiles
import os
from typing import Tuple

async def save_upload_file(upload_file: UploadFile, save_path: str) -> str:
    """
    Save an uploaded file to the specified path
    """
    try:
        async with aiofiles.open(save_path, 'wb') as out_file:
            content = await upload_file.read()
            await out_file.write(content)
        return save_path
    except Exception as e:
        raise Exception(f"Error saving file: {str(e)}")

async def read_file_content(file_path: str) -> bytes:
    """
    Read file content as bytes
    """
    try:
        async with aiofiles.open(file_path, 'rb') as file:
            return await file.read()
    except Exception as e:
        raise Exception(f"Error reading file: {str(e)}")

def get_file_extension(filename: str) -> str:
    """
    Get file extension from filename
    """
    return os.path.splitext(filename)[1].lower() 