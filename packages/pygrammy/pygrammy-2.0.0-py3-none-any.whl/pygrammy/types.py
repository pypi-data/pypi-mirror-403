from dataclasses import dataclass
from typing import Optional, List, Dict, Any


@dataclass
class User:
    id: int
    is_bot: bool
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None
    language_code: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict):
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})


@dataclass
class Chat:
    id: int
    type: str
    title: Optional[str] = None
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    description: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict):
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})


@dataclass
class MessageEntity:
    type: str
    offset: int
    length: int
    url: Optional[str] = None
    user: Optional[User] = None
    
    @classmethod
    def from_dict(cls, data: Dict):
        if "user" in data:
            data["user"] = User.from_dict(data["user"])
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})


@dataclass
class PhotoSize:
    file_id: str
    file_unique_id: str
    width: int
    height: int
    file_size: Optional[int] = None
    
    @classmethod
    def from_dict(cls, data: Dict):
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})


@dataclass
class Audio:
    """Audio file"""
    file_id: str
    file_unique_id: str
    duration: int
    performer: Optional[str] = None
    title: Optional[str] = None
    file_name: Optional[str] = None
    mime_type: Optional[str] = None
    file_size: Optional[int] = None
    
    @classmethod
    def from_dict(cls, data: Dict):
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})


@dataclass
class Document:
    """General file (document)"""
    file_id: str
    file_unique_id: str
    file_name: Optional[str] = None
    mime_type: Optional[str] = None
    file_size: Optional[int] = None
    
    @classmethod
    def from_dict(cls, data: Dict):
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})


@dataclass
class Video:
    """Video file"""
    file_id: str
    file_unique_id: str
    width: int
    height: int
    duration: int
    file_name: Optional[str] = None
    mime_type: Optional[str] = None
    file_size: Optional[int] = None
    
    @classmethod
    def from_dict(cls, data: Dict):
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})


@dataclass
class Animation:
    """Animation file (GIF or H.264/MPEG-4 AVC video without sound)"""
    file_id: str
    file_unique_id: str
    width: int
    height: int
    duration: int
    file_name: Optional[str] = None
    mime_type: Optional[str] = None
    file_size: Optional[int] = None
    
    @classmethod
    def from_dict(cls, data: Dict):
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})


@dataclass
class Voice:
    """Voice message"""
    file_id: str
    file_unique_id: str
    duration: int
    mime_type: Optional[str] = None
    file_size: Optional[int] = None
    
    @classmethod
    def from_dict(cls, data: Dict):
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})


@dataclass
class VideoNote:
    """Video message (note)"""
    file_id: str
    file_unique_id: str
    length: int
    duration: int
    file_size: Optional[int] = None
    
    @classmethod
    def from_dict(cls, data: Dict):
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})


@dataclass
class Sticker:
    """Sticker"""
    file_id: str
    file_unique_id: str
    width: int
    height: int
    is_animated: bool
    is_video: bool
    emoji: Optional[str] = None
    set_name: Optional[str] = None
    file_size: Optional[int] = None
    
    @classmethod
    def from_dict(cls, data: Dict):
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})


@dataclass
class Location:
    """Geographic location"""
    longitude: float
    latitude: float
    horizontal_accuracy: Optional[float] = None
    
    @classmethod
    def from_dict(cls, data: Dict):
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})


@dataclass
class Venue:
    """Venue"""
    location: Location
    title: str
    address: str
    foursquare_id: Optional[str] = None
    foursquare_type: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict):
        data = data.copy()
        if "location" in data:
            data["location"] = Location.from_dict(data["location"])
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})


@dataclass
class Contact:
    """Contact"""
    phone_number: str
    first_name: str
    last_name: Optional[str] = None
    user_id: Optional[int] = None
    
    @classmethod
    def from_dict(cls, data: Dict):
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})


@dataclass
class PollOption:
    """Poll option"""
    text: str
    voter_count: int
    
    @classmethod
    def from_dict(cls, data: Dict):
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})


@dataclass
class Poll:
    """Poll"""
    id: str
    question: str
    options: List[PollOption]
    total_voter_count: int
    is_closed: bool
    is_anonymous: bool
    type: str
    allows_multiple_answers: bool
    
    @classmethod
    def from_dict(cls, data: Dict):
        data = data.copy()
        if "options" in data:
            data["options"] = [PollOption.from_dict(opt) for opt in data["options"]]
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})


@dataclass
class Dice:
    """Dice"""
    emoji: str
    value: int
    
    @classmethod
    def from_dict(cls, data: Dict):
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})


@dataclass
class File:
    """File information"""
    file_id: str
    file_unique_id: str
    file_size: Optional[int] = None
    file_path: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict):
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})


@dataclass
class Message:
    message_id: int
    date: int
    chat: Chat
    from_user: Optional[User] = None
    text: Optional[str] = None
    caption: Optional[str] = None
    entities: Optional[List[MessageEntity]] = None
    photo: Optional[List[PhotoSize]] = None
    video: Optional[Video] = None
    audio: Optional[Audio] = None
    document: Optional[Document] = None
    animation: Optional[Animation] = None
    voice: Optional[Voice] = None
    video_note: Optional[VideoNote] = None
    sticker: Optional[Sticker] = None
    location: Optional[Location] = None
    venue: Optional[Venue] = None
    contact: Optional[Contact] = None
    poll: Optional[Poll] = None
    dice: Optional[Dice] = None
    reply_to_message: Optional['Message'] = None
    forward_from: Optional[User] = None
    forward_from_chat: Optional[Chat] = None
    forward_date: Optional[int] = None
    
    @classmethod
    def from_dict(cls, data: Dict):
        data = data.copy()
        
        if "from" in data:
            data["from_user"] = User.from_dict(data.pop("from"))
        
        if "chat" in data:
            data["chat"] = Chat.from_dict(data["chat"])
        
        if "entities" in data:
            data["entities"] = [MessageEntity.from_dict(e) for e in data["entities"]]
        
        if "photo" in data:
            data["photo"] = [PhotoSize.from_dict(p) for p in data["photo"]]
        
        if "video" in data and isinstance(data["video"], dict):
            data["video"] = Video.from_dict(data["video"])
        
        if "audio" in data and isinstance(data["audio"], dict):
            data["audio"] = Audio.from_dict(data["audio"])
        
        if "document" in data and isinstance(data["document"], dict):
            data["document"] = Document.from_dict(data["document"])
        
        if "animation" in data and isinstance(data["animation"], dict):
            data["animation"] = Animation.from_dict(data["animation"])
        
        if "voice" in data and isinstance(data["voice"], dict):
            data["voice"] = Voice.from_dict(data["voice"])
        
        if "video_note" in data and isinstance(data["video_note"], dict):
            data["video_note"] = VideoNote.from_dict(data["video_note"])
        
        if "sticker" in data and isinstance(data["sticker"], dict):
            data["sticker"] = Sticker.from_dict(data["sticker"])
        
        if "location" in data and isinstance(data["location"], dict):
            data["location"] = Location.from_dict(data["location"])
        
        if "venue" in data and isinstance(data["venue"], dict):
            data["venue"] = Venue.from_dict(data["venue"])
        
        if "contact" in data and isinstance(data["contact"], dict):
            data["contact"] = Contact.from_dict(data["contact"])
        
        if "poll" in data and isinstance(data["poll"], dict):
            data["poll"] = Poll.from_dict(data["poll"])
        
        if "dice" in data and isinstance(data["dice"], dict):
            data["dice"] = Dice.from_dict(data["dice"])
        
        if "reply_to_message" in data:
            data["reply_to_message"] = Message.from_dict(data["reply_to_message"])
        
        if "forward_from" in data:
            data["forward_from"] = User.from_dict(data["forward_from"])
        
        if "forward_from_chat" in data:
            data["forward_from_chat"] = Chat.from_dict(data["forward_from_chat"])
        
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})


@dataclass
class CallbackQuery:
    id: str
    from_user: User
    data: Optional[str] = None
    message: Optional[Message] = None
    inline_message_id: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict):
        data = data.copy()
        
        if "from" in data:
            data["from_user"] = User.from_dict(data.pop("from"))
        
        if "message" in data:
            data["message"] = Message.from_dict(data["message"])
        
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})


@dataclass
class InlineQuery:
    """Inline query"""
    id: str
    from_user: User
    query: str
    offset: str
    chat_type: Optional[str] = None
    location: Optional[Location] = None
    
    @classmethod
    def from_dict(cls, data: Dict):
        data = data.copy()
        
        if "from" in data:
            data["from_user"] = User.from_dict(data.pop("from"))
        
        if "location" in data and isinstance(data["location"], dict):
            data["location"] = Location.from_dict(data["location"])
        
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})


@dataclass
class ChosenInlineResult:
    """Chosen inline result"""
    result_id: str
    from_user: User
    query: str
    location: Optional[Location] = None
    inline_message_id: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict):
        data = data.copy()
        
        if "from" in data:
            data["from_user"] = User.from_dict(data.pop("from"))
        
        if "location" in data and isinstance(data["location"], dict):
            data["location"] = Location.from_dict(data["location"])
        
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})


@dataclass
class ChatMemberUpdated:
    """Chat member status was updated"""
    chat: Chat
    from_user: User
    date: int
    old_chat_member: Dict
    new_chat_member: Dict
    
    @classmethod
    def from_dict(cls, data: Dict):
        data = data.copy()
        
        if "chat" in data:
            data["chat"] = Chat.from_dict(data["chat"])
        
        if "from" in data:
            data["from_user"] = User.from_dict(data.pop("from"))
        
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})


@dataclass
class Update:
    update_id: int
    message: Optional[Message] = None
    edited_message: Optional[Message] = None
    callback_query: Optional[CallbackQuery] = None
    inline_query: Optional[InlineQuery] = None
    chosen_inline_result: Optional[ChosenInlineResult] = None
    poll: Optional[Poll] = None
    poll_answer: Optional[Dict] = None
    my_chat_member: Optional[ChatMemberUpdated] = None
    chat_member: Optional[ChatMemberUpdated] = None
    
    @classmethod
    def from_dict(cls, data: Dict):
        data = data.copy()
        
        if "message" in data:
            data["message"] = Message.from_dict(data["message"])
        
        if "edited_message" in data:
            data["edited_message"] = Message.from_dict(data["edited_message"])
        
        if "callback_query" in data:
            data["callback_query"] = CallbackQuery.from_dict(data["callback_query"])
        
        if "inline_query" in data:
            data["inline_query"] = InlineQuery.from_dict(data["inline_query"])
        
        if "chosen_inline_result" in data:
            data["chosen_inline_result"] = ChosenInlineResult.from_dict(data["chosen_inline_result"])
        
        if "poll" in data and isinstance(data["poll"], dict):
            data["poll"] = Poll.from_dict(data["poll"])
        
        if "my_chat_member" in data:
            data["my_chat_member"] = ChatMemberUpdated.from_dict(data["my_chat_member"])
        
        if "chat_member" in data:
            data["chat_member"] = ChatMemberUpdated.from_dict(data["chat_member"])
        
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})