from typing import List, Optional, Dict, Any


class InlineKeyboard:
    """
    Inline keyboard (xabar ostida ko'rinadigan tugmalar)
    
    Example:
        kb = InlineKeyboard()
        kb.text("👍 Like", "like").text("👎 Dislike", "dislike")
        kb.row()
        kb.url("Google", "https://google.com")
    """

    def __init__(self):
        self.keyboard: List[List[Dict]] = [[]]

    def text(self, text: str, callback_data: str):
        """Oddiy tugma"""
        self.keyboard[-1].append({
            "text": text,
            "callback_data": callback_data,
        })
        return self

    def url(self, text: str, url: str):
        """URL tugma"""
        self.keyboard[-1].append({
            "text": text,
            "url": url,
        })
        return self

    def web_app(self, text: str, url: str):
        """Web App tugma"""
        self.keyboard[-1].append({
            "text": text,
            "web_app": {"url": url},
        })
        return self
    
    def switch_inline_query(self, text: str, query: str = ""):
        """Inline query tugma (joriy chatda)"""
        self.keyboard[-1].append({
            "text": text,
            "switch_inline_query": query,
        })
        return self
    
    def switch_inline_query_current_chat(self, text: str, query: str = ""):
        """Inline query tugma (boshqa chatda)"""
        self.keyboard[-1].append({
            "text": text,
            "switch_inline_query_current_chat": query,
        })
        return self
    
    def login_url(self, text: str, url: str):
        """Login URL tugma"""
        self.keyboard[-1].append({
            "text": text,
            "login_url": {"url": url},
        })
        return self
    
    def pay(self, text: str):
        """To'lov tugma"""
        self.keyboard[-1].append({
            "text": text,
            "pay": True,
        })
        return self

    def row(self):
        """Yangi qator boshlash"""
        if self.keyboard[-1]:  # Agar oxirgi qator bo'sh bo'lmasa
            self.keyboard.append([])
        return self

    def to_dict(self) -> Dict:
        """Dict formatga o'tkazish"""
        # Bo'sh qatorlarni olib tashlash
        keyboard = [row for row in self.keyboard if row]
        return {"inline_keyboard": keyboard}


class Keyboard:
    """
    Reply keyboard (klaviatura tugmalari)
    
    Example:
        kb = Keyboard()
        kb.text("Profil").text("Sozlamalar")
        kb.row()
        kb.text("Yordam")
        kb.resized()
    """

    def __init__(self):
        self.keyboard: List[List[Dict]] = [[]]
        self._resize_keyboard = False
        self._one_time_keyboard = False
        self._selective = False
        self._input_field_placeholder = None

    def text(self, text: str):
        """Matn tugma"""
        self.keyboard[-1].append({"text": text})
        return self

    def request_contact(self, text: str):
        """Kontakt so'rash"""
        self.keyboard[-1].append({
            "text": text,
            "request_contact": True,
        })
        return self

    def request_location(self, text: str):
        """Joylashuvni so'rash"""
        self.keyboard[-1].append({
            "text": text,
            "request_location": True,
        })
        return self
    
    def request_poll(self, text: str, type: Optional[str] = None):
        """Poll so'rash"""
        button = {
            "text": text,
            "request_poll": {}
        }
        if type:
            button["request_poll"]["type"] = type
        self.keyboard[-1].append(button)
        return self

    def row(self):
        """Yangi qator"""
        if self.keyboard[-1]:
            self.keyboard.append([])
        return self

    def resized(self, resize: bool = True):
        """Avtomatik o'lchamga moslashtirish"""
        self._resize_keyboard = resize
        return self

    def one_time(self, one_time: bool = True):
        """Bir marta ko'rsatish"""
        self._one_time_keyboard = one_time
        return self
    
    def placeholder(self, text: str):
        """Input field placeholder"""
        self._input_field_placeholder = text
        return self

    def selective(self, selective: bool = True):
        """Faqat ba'zi foydalanuvchilarga ko'rsatish"""
        self._selective = selective
        return self

    def to_dict(self) -> Dict:
        """Dict formatga o'tkazish"""
        keyboard = [row for row in self.keyboard if row]
        result = {"keyboard": keyboard}
        
        if self._resize_keyboard:
            result["resize_keyboard"] = True
        if self._one_time_keyboard:
            result["one_time_keyboard"] = True
        if self._selective:
            result["selective"] = True
        if self._input_field_placeholder:
            result["input_field_placeholder"] = self._input_field_placeholder
        
        return result


class RemoveKeyboard:
    """Klaviaturani olib tashlash"""
    
    def __init__(self, selective: bool = False):
        self.selective = selective
    
    def to_dict(self) -> Dict:
        result = {"remove_keyboard": True}
        if self.selective:
            result["selective"] = True
        return result


class ForceReply:
    """
    Foydalanuvchini javob berishga majbur qilish
    
    Example:
        await ctx.reply("Ismingiz nima?", reply_markup=ForceReply())
    """
    
    def __init__(
        self,
        selective: bool = False,
        input_field_placeholder: Optional[str] = None
    ):
        self.selective = selective
        self.input_field_placeholder = input_field_placeholder
    
    def to_dict(self) -> Dict:
        result = {"force_reply": True}
        if self.selective:
            result["selective"] = True
        if self.input_field_placeholder:
            result["input_field_placeholder"] = self.input_field_placeholder
        return result
