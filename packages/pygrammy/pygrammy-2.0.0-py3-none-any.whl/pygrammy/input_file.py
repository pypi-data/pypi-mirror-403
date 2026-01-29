"""
InputFile - File handling for PyGrammY
Supports local files, URLs, bytes, and file objects
"""

from typing import Union, Optional, BinaryIO
from pathlib import Path
import mimetypes


class InputFile:
    """
    File input uchun helper class
    
    Examples:
        # Local file
        photo = InputFile("photo.jpg")
        await ctx.replyWithPhoto(photo)
        
        # URL
        photo = InputFile.from_url("https://example.com/photo.jpg")
        
        # Bytes
        photo = InputFile(photo_bytes, filename="photo.jpg")
    """
    
    def __init__(
        self,
        file: Union[str, bytes, BinaryIO, Path],
        filename: Optional[str] = None,
    ):
        self.file = file
        self.filename = filename
        
        # Agar file path bo'lsa, filename'ni aniqlash
        if isinstance(file, (str, Path)) and not filename:
            path = Path(file)
            if path.exists() and path.is_file():
                self.filename = path.name
        
        # MIME type aniqlash
        self.mime_type = None
        if self.filename:
            self.mime_type = mimetypes.guess_type(self.filename)[0]
    
    @classmethod
    def from_url(cls, url: str, filename: Optional[str] = None):
        """URL dan InputFile yaratish"""
        if not filename:
            filename = url.split('/')[-1].split('?')[0]
        return cls(url, filename=filename)
    
    def to_dict(self):
        """API uchun dict formatga o'tkazish"""
        # Agar file_id yoki URL bo'lsa, string qaytarish
        if isinstance(self.file, str):
            # Check if it's a file_id or URL
            if self.file.startswith(('http://', 'https://')):
                return self.file
            # Check if it's a local file path
            path = Path(self.file)
            if path.exists():
                return ('file', open(self.file, 'rb'), self.mime_type)
            # Otherwise assume it's a file_id
            return self.file
        
        # Agar bytes bo'lsa
        if isinstance(self.file, bytes):
            return ('file', self.file, self.mime_type)
        
        # Agar file object bo'lsa
        if hasattr(self.file, 'read'):
            return ('file', self.file, self.mime_type)
        
        return self.file
    
    def __str__(self):
        return f"InputFile({self.filename or 'unnamed'})"
    
    def __repr__(self):
        return self.__str__()


class InputMediaPhoto:
    """Media group uchun photo"""
    
    def __init__(
        self,
        media: Union[str, InputFile],
        caption: Optional[str] = None,
        parse_mode: Optional[str] = None,
    ):
        self.type = "photo"
        self.media = media
        self.caption = caption
        self.parse_mode = parse_mode
    
    def to_dict(self):
        result = {"type": self.type}
        
        if isinstance(self.media, InputFile):
            result["media"] = self.media.to_dict()
        else:
            result["media"] = self.media
        
        if self.caption:
            result["caption"] = self.caption
        if self.parse_mode:
            result["parse_mode"] = self.parse_mode
        
        return result


class InputMediaVideo:
    """Media group uchun video"""
    
    def __init__(
        self,
        media: Union[str, InputFile],
        caption: Optional[str] = None,
        parse_mode: Optional[str] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        duration: Optional[int] = None,
    ):
        self.type = "video"
        self.media = media
        self.caption = caption
        self.parse_mode = parse_mode
        self.width = width
        self.height = height
        self.duration = duration
    
    def to_dict(self):
        result = {"type": self.type}
        
        if isinstance(self.media, InputFile):
            result["media"] = self.media.to_dict()
        else:
            result["media"] = self.media
        
        if self.caption:
            result["caption"] = self.caption
        if self.parse_mode:
            result["parse_mode"] = self.parse_mode
        if self.width:
            result["width"] = self.width
        if self.height:
            result["height"] = self.height
        if self.duration:
            result["duration"] = self.duration
        
        return result


class InputMediaAudio:
    """Media group uchun audio"""
    
    def __init__(
        self,
        media: Union[str, InputFile],
        caption: Optional[str] = None,
        parse_mode: Optional[str] = None,
        duration: Optional[int] = None,
        performer: Optional[str] = None,
        title: Optional[str] = None,
    ):
        self.type = "audio"
        self.media = media
        self.caption = caption
        self.parse_mode = parse_mode
        self.duration = duration
        self.performer = performer
        self.title = title
    
    def to_dict(self):
        result = {"type": self.type}
        
        if isinstance(self.media, InputFile):
            result["media"] = self.media.to_dict()
        else:
            result["media"] = self.media
        
        if self.caption:
            result["caption"] = self.caption
        if self.parse_mode:
            result["parse_mode"] = self.parse_mode
        if self.duration:
            result["duration"] = self.duration
        if self.performer:
            result["performer"] = self.performer
        if self.title:
            result["title"] = self.title
        
        return result


class InputMediaDocument:
    """Media group uchun document"""
    
    def __init__(
        self,
        media: Union[str, InputFile],
        caption: Optional[str] = None,
        parse_mode: Optional[str] = None,
    ):
        self.type = "document"
        self.media = media
        self.caption = caption
        self.parse_mode = parse_mode
    
    def to_dict(self):
        result = {"type": self.type}
        
        if isinstance(self.media, InputFile):
            result["media"] = self.media.to_dict()
        else:
            result["media"] = self.media
        
        if self.caption:
            result["caption"] = self.caption
        if self.parse_mode:
            result["parse_mode"] = self.parse_mode
        
        return result
