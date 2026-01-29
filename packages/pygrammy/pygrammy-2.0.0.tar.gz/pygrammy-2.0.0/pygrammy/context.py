from typing import Optional, Dict, Any, Union, List
from .types import Update, Message, CallbackQuery, Chat, User
from .keyboard import InlineKeyboard, Keyboard, RemoveKeyboard, ForceReply
from .input_file import InputFile, InputMediaPhoto, InputMediaVideo, InputMediaAudio, InputMediaDocument
import httpx


class Context:
    """
    Context - har bir update uchun yaratiladi
    GrammyJS ctx ga o'xshash
    """

    def __init__(self, bot, update: Update):
        self.bot = bot
        self.update = update
        
        # State (vaqtinchalik ma'lumotlar)
        self.state: Dict[str, Any] = {}
        
        # Session (middleware orqali qo'shiladi)
        self.session: Optional[Dict] = None

    # ==================== Update qismlari ====================

    @property
    def message(self) -> Optional[Message]:
        """Kelgan xabar"""
        return self.update.message

    @property
    def edited_message(self) -> Optional[Message]:
        """O'zgartirilgan xabar"""
        return self.update.edited_message

    @property
    def callback_query(self) -> Optional[CallbackQuery]:
        """Callback query"""
        return self.update.callback_query
    
    @property
    def inline_query(self):
        """Inline query"""
        return self.update.inline_query
    
    @property
    def chosen_inline_result(self):
        """Chosen inline result"""
        return self.update.chosen_inline_result

    @property
    def chat(self) -> Optional[Chat]:
        """Chat obyekti"""
        if self.message:
            return self.message.chat
        elif self.callback_query and self.callback_query.message:
            return self.callback_query.message.chat
        return None

    @property
    def from_user(self) -> Optional[User]:
        """Xabar yuborgan foydalanuvchi"""
        if self.message:
            return self.message.from_user
        elif self.callback_query:
            return self.callback_query.from_user
        elif self.inline_query:
            return self.inline_query.from_user
        return None

    @property
    def chat_id(self) -> Optional[int]:
        """Chat ID"""
        if self.chat:
            return self.chat.id
        return None

    # ==================== API metodlar (ctx.api) ====================

    @property
    def api(self):
        """API metodlariga to'g'ridan-to'g'ri kirish"""
        return self.bot

    # ==================== Javob metodlari ====================

    async def reply(
        self,
        text: str,
        reply_markup: Optional[Union[InlineKeyboard, Keyboard, RemoveKeyboard, ForceReply]] = None,
        parse_mode: Optional[str] = None,
        disable_web_page_preview: Optional[bool] = None,
        **kwargs
    ):
        """
        Xabarga javob berish
        
        Example:
            await ctx.reply("Salom!", parse_mode="HTML")
        """
        params = {
            "chat_id": self.chat_id,
            "text": text,
            **kwargs
        }
        
        if reply_markup:
            params["reply_markup"] = reply_markup.to_dict()
        
        if parse_mode:
            params["parse_mode"] = parse_mode
        
        if disable_web_page_preview:
            params["disable_web_page_preview"] = disable_web_page_preview
        
        return await self.bot.api_request("sendMessage", params)

    async def sendMessage(self, text: str, **kwargs):
        """Xabar yuborish (reply bilan bir xil)"""
        return await self.reply(text, **kwargs)

    # ==================== Media yuborish metodlari ====================

    async def replyWithPhoto(
        self,
        photo: Union[str, InputFile],
        caption: Optional[str] = None,
        reply_markup: Optional[Union[InlineKeyboard, Keyboard]] = None,
        parse_mode: Optional[str] = None,
        **kwargs
    ):
        """Rasm yuborish (GrammyJS uslubida)"""
        return await self.sendPhoto(photo, caption, reply_markup, parse_mode, **kwargs)

    async def sendPhoto(
        self,
        photo: Union[str, InputFile],
        caption: Optional[str] = None,
        reply_markup: Optional[Union[InlineKeyboard, Keyboard]] = None,
        parse_mode: Optional[str] = None,
        **kwargs
    ):
        """Rasm yuborish"""
        params = {
            "chat_id": self.chat_id,
            **kwargs
        }
        
        if caption:
            params["caption"] = caption
        
        if parse_mode:
            params["parse_mode"] = parse_mode
        
        if reply_markup:
            params["reply_markup"] = reply_markup.to_dict()
        
        # Handle InputFile
        files = None
        if isinstance(photo, InputFile):
            file_data = photo.to_dict()
            if isinstance(file_data, tuple):
                files = {"photo": file_data}
                params["photo"] = "attach://photo"
            else:
                params["photo"] = file_data
        else:
            params["photo"] = photo
        
        return await self.bot.api_request("sendPhoto", params, files=files)

    async def replyWithVideo(self, video: Union[str, InputFile], **kwargs):
        """Video yuborish (GrammyJS uslubida)"""
        return await self.sendVideo(video, **kwargs)

    async def sendVideo(
        self,
        video: Union[str, InputFile],
        caption: Optional[str] = None,
        reply_markup: Optional[Union[InlineKeyboard, Keyboard]] = None,
        **kwargs
    ):
        """Video yuborish"""
        params = {
            "chat_id": self.chat_id,
            **kwargs
        }
        
        if caption:
            params["caption"] = caption
        
        if reply_markup:
            params["reply_markup"] = reply_markup.to_dict()
        
        files = None
        if isinstance(video, InputFile):
            file_data = video.to_dict()
            if isinstance(file_data, tuple):
                files = {"video": file_data}
                params["video"] = "attach://video"
            else:
                params["video"] = file_data
        else:
            params["video"] = video
        
        return await self.bot.api_request("sendVideo", params, files=files)

    async def replyWithAudio(self, audio: Union[str, InputFile], **kwargs):
        """Audio yuborish (GrammyJS uslubida)"""
        return await self.sendAudio(audio, **kwargs)

    async def sendAudio(
        self,
        audio: Union[str, InputFile],
        caption: Optional[str] = None,
        **kwargs
    ):
        """Audio yuborish"""
        params = {
            "chat_id": self.chat_id,
            **kwargs
        }
        
        if caption:
            params["caption"] = caption
        
        files = None
        if isinstance(audio, InputFile):
            file_data = audio.to_dict()
            if isinstance(file_data, tuple):
                files = {"audio": file_data}
                params["audio"] = "attach://audio"
            else:
                params["audio"] = file_data
        else:
            params["audio"] = audio
        
        return await self.bot.api_request("sendAudio", params, files=files)

    async def replyWithDocument(self, document: Union[str, InputFile], **kwargs):
        """Document yuborish (GrammyJS uslubida)"""
        return await self.sendDocument(document, **kwargs)

    async def sendDocument(
        self,
        document: Union[str, InputFile],
        caption: Optional[str] = None,
        **kwargs
    ):
        """Fayl yuborish"""
        params = {
            "chat_id": self.chat_id,
            **kwargs
        }
        
        if caption:
            params["caption"] = caption
        
        files = None
        if isinstance(document, InputFile):
            file_data = document.to_dict()
            if isinstance(file_data, tuple):
                files = {"document": file_data}
                params["document"] = "attach://document"
            else:
                params["document"] = file_data
        else:
            params["document"] = document
        
        return await self.bot.api_request("sendDocument", params, files=files)

    async def sendVoice(self, voice: Union[str, InputFile], **kwargs):
        """Voice yuborish"""
        params = {"chat_id": self.chat_id, **kwargs}
        
        files = None
        if isinstance(voice, InputFile):
            file_data = voice.to_dict()
            if isinstance(file_data, tuple):
                files = {"voice": file_data}
                params["voice"] = "attach://voice"
            else:
                params["voice"] = file_data
        else:
            params["voice"] = voice
        
        return await self.bot.api_request("sendVoice", params, files=files)

    async def sendVideoNote(self, video_note: Union[str, InputFile], **kwargs):
        """Video note yuborish"""
        params = {"chat_id": self.chat_id, **kwargs}
        
        files = None
        if isinstance(video_note, InputFile):
            file_data = video_note.to_dict()
            if isinstance(file_data, tuple):
                files = {"video_note": file_data}
                params["video_note"] = "attach://video_note"
            else:
                params["video_note"] = file_data
        else:
            params["video_note"] = video_note
        
        return await self.bot.api_request("sendVideoNote", params, files=files)

    async def sendSticker(self, sticker: Union[str, InputFile], **kwargs):
        """Sticker yuborish"""
        params = {"chat_id": self.chat_id, **kwargs}
        
        files = None
        if isinstance(sticker, InputFile):
            file_data = sticker.to_dict()
            if isinstance(file_data, tuple):
                files = {"sticker": file_data}
                params["sticker"] = "attach://sticker"
            else:
                params["sticker"] = file_data
        else:
            params["sticker"] = sticker
        
        return await self.bot.api_request("sendSticker", params, files=files)

    async def sendMediaGroup(
        self,
        media: List[Union[InputMediaPhoto, InputMediaVideo, InputMediaAudio, InputMediaDocument]],
        **kwargs
    ):
        """Media group yuborish"""
        params = {
            "chat_id": self.chat_id,
            "media": [m.to_dict() for m in media],
            **kwargs
        }
        return await self.bot.api_request("sendMediaGroup", params)

    async def sendLocation(
        self,
        latitude: float,
        longitude: float,
        **kwargs
    ):
        """Joylashuv yuborish"""
        params = {
            "chat_id": self.chat_id,
            "latitude": latitude,
            "longitude": longitude,
            **kwargs
        }
        return await self.bot.api_request("sendLocation", params)

    async def sendVenue(
        self,
        latitude: float,
        longitude: float,
        title: str,
        address: str,
        **kwargs
    ):
        """Venue yuborish"""
        params = {
            "chat_id": self.chat_id,
            "latitude": latitude,
            "longitude": longitude,
            "title": title,
            "address": address,
            **kwargs
        }
        return await self.bot.api_request("sendVenue", params)

    async def sendContact(
        self,
        phone_number: str,
        first_name: str,
        **kwargs
    ):
        """Kontakt yuborish"""
        params = {
            "chat_id": self.chat_id,
            "phone_number": phone_number,
            "first_name": first_name,
            **kwargs
        }
        return await self.bot.api_request("sendContact", params)

    async def sendPoll(
        self,
        question: str,
        options: List[str],
        is_anonymous: bool = True,
        **kwargs
    ):
        """Poll yuborish"""
        params = {
            "chat_id": self.chat_id,
            "question": question,
            "options": options,
            "is_anonymous": is_anonymous,
            **kwargs
        }
        return await self.bot.api_request("sendPoll", params)

    async def sendDice(self, emoji: str = "🎲", **kwargs):
        """Dice yuborish"""
        params = {
            "chat_id": self.chat_id,
            "emoji": emoji,
            **kwargs
        }
        return await self.bot.api_request("sendDice", params)

    # ==================== Chat Actions ====================

    async def sendChatAction(self, action: str):
        """
        Chat action yuborish (typing, upload_photo, va boshqalar)
        
        Actions: typing, upload_photo, record_video, upload_video, 
                 record_voice, upload_voice, upload_document, 
                 choose_sticker, find_location, record_video_note, 
                 upload_video_note
        """
        return await self.bot.api_request("sendChatAction", {
            "chat_id": self.chat_id,
            "action": action,
        })
    
    async def replyWithChatAction(self, action: str):
        """GrammyJS uslubida chat action"""
        return await self.sendChatAction(action)

    # ==================== Message Operations ====================

    async def forwardMessage(
        self,
        from_chat_id: Union[int, str],
        message_id: int,
        **kwargs
    ):
        """Xabarni forward qilish"""
        params = {
            "chat_id": self.chat_id,
            "from_chat_id": from_chat_id,
            "message_id": message_id,
            **kwargs
        }
        return await self.bot.api_request("forwardMessage", params)

    async def copyMessage(
        self,
        from_chat_id: Union[int, str],
        message_id: int,
        **kwargs
    ):
        """Xabarni nusxalash (forward signature'siz)"""
        params = {
            "chat_id": self.chat_id,
            "from_chat_id": from_chat_id,
            "message_id": message_id,
            **kwargs
        }
        return await self.bot.api_request("copyMessage", params)

    async def pinChatMessage(self, message_id: Optional[int] = None, **kwargs):
        """Xabarni pin qilish"""
        msg_id = message_id or (self.message.message_id if self.message else None)
        if not msg_id:
            raise ValueError("No message to pin")
        
        params = {
            "chat_id": self.chat_id,
            "message_id": msg_id,
            **kwargs
        }
        return await self.bot.api_request("pinChatMessage", params)

    async def unpinChatMessage(self, message_id: Optional[int] = None):
        """Xabarni unpin qilish"""
        params = {"chat_id": self.chat_id}
        if message_id:
            params["message_id"] = message_id
        
        return await self.bot.api_request("unpinChatMessage", params)

    async def unpinAllChatMessages(self):
        """Barcha xabarlarni unpin qilish"""
        return await self.bot.api_request("unpinAllChatMessages", {
            "chat_id": self.chat_id,
        })

    # ==================== Callback Query ====================

    async def answerCallbackQuery(
        self,
        text: Optional[str] = None,
        show_alert: bool = False,
        **kwargs
    ):
        """Callback query ga javob berish (GrammyJS uslubida)"""
        return await self.answer_callback_query(text, show_alert, **kwargs)

    async def answer_callback_query(
        self,
        text: Optional[str] = None,
        show_alert: bool = False,
        **kwargs
    ):
        """
        Callback query ga javob berish
        
        Example:
            await ctx.answer_callback_query("Muvaffaqiyatli!")
        """
        if not self.callback_query:
            raise ValueError("No callback query to answer")
        
        params = {
            "callback_query_id": self.callback_query.id,
            **kwargs
        }
        
        if text:
            params["text"] = text
        
        if show_alert:
            params["show_alert"] = show_alert
        
        return await self.bot.api_request("answerCallbackQuery", params)

    # ==================== Inline Query ====================

    async def answerInlineQuery(
        self,
        results: List[Dict],
        cache_time: int = 300,
        **kwargs
    ):
        """Inline query ga javob berish"""
        if not self.inline_query:
            raise ValueError("No inline query to answer")
        
        params = {
            "inline_query_id": self.inline_query.id,
            "results": results,
            "cache_time": cache_time,
            **kwargs
        }
        return await self.bot.api_request("answerInlineQuery", params)

    # ==================== Message Editing ====================

    async def editMessageText(
        self,
        text: str,
        reply_markup: Optional[InlineKeyboard] = None,
        parse_mode: Optional[str] = None,
        **kwargs
    ):
        """Xabar matnini o'zgartirish (GrammyJS uslubida)"""
        return await self.edit_message_text(text, reply_markup, parse_mode, **kwargs)

    async def edit_message_text(
        self,
        text: str,
        reply_markup: Optional[InlineKeyboard] = None,
        parse_mode: Optional[str] = None,
        **kwargs
    ):
        """Xabar matnini o'zgartirish"""
        params = {
            "chat_id": self.chat_id,
            "text": text,
            **kwargs
        }
        
        if self.callback_query and self.callback_query.message:
            params["message_id"] = self.callback_query.message.message_id
        elif self.message:
            params["message_id"] = self.message.message_id
        
        if reply_markup:
            params["reply_markup"] = reply_markup.to_dict()
        
        if parse_mode:
            params["parse_mode"] = parse_mode
        
        return await self.bot.api_request("editMessageText", params)

    async def editMessageReplyMarkup(
        self,
        reply_markup: Optional[InlineKeyboard] = None,
        **kwargs
    ):
        """Xabar tugmalarini o'zgartirish (GrammyJS uslubida)"""
        return await self.edit_message_reply_markup(reply_markup, **kwargs)

    async def edit_message_reply_markup(
        self,
        reply_markup: Optional[InlineKeyboard] = None,
        **kwargs
    ):
        """Xabar tugmalarini o'zgartirish"""
        params = {"chat_id": self.chat_id, **kwargs}
        
        if self.callback_query and self.callback_query.message:
            params["message_id"] = self.callback_query.message.message_id
        elif self.message:
            params["message_id"] = self.message.message_id
        
        if reply_markup:
            params["reply_markup"] = reply_markup.to_dict()
        
        return await self.bot.api_request("editMessageReplyMarkup", params)

    async def editMessageCaption(
        self,
        caption: str,
        reply_markup: Optional[InlineKeyboard] = None,
        **kwargs
    ):
        """Media caption'ni o'zgartirish"""
        params = {
            "chat_id": self.chat_id,
            "caption": caption,
            **kwargs
        }
        
        if self.callback_query and self.callback_query.message:
            params["message_id"] = self.callback_query.message.message_id
        elif self.message:
            params["message_id"] = self.message.message_id
        
        if reply_markup:
            params["reply_markup"] = reply_markup.to_dict()
        
        return await self.bot.api_request("editMessageCaption", params)

    async def deleteMessage(self, message_id: Optional[int] = None):
        """Xabarni o'chirish"""
        msg_id = message_id or (self.message.message_id if self.message else None)
        
        if not msg_id:
            raise ValueError("No message to delete")
        
        return await self.bot.api_request("deleteMessage", {
            "chat_id": self.chat_id,
            "message_id": msg_id,
        })

    # ==================== File Operations ====================

    async def getFile(self, file_id: str):
        """Fayl haqida ma'lumot olish"""
        return await self.bot.api_request("getFile", {"file_id": file_id})
    
    async def downloadFile(self, file_id: str, destination: Optional[str] = None):
        """
        Faylni yuklab olish
        
        Example:
            file_info = await ctx.getFile(ctx.message.document.file_id)
            await ctx.downloadFile(file_info['file_id'], 'downloads/file.pdf')
        """
        file_info = await self.getFile(file_id)
        file_path = file_info.get("file_path")
        
        if not file_path:
            raise ValueError("File path not found")
        
        # Download file
        file_url = f"https://api.telegram.org/file/bot{self.bot.token}/{file_path}"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(file_url)
            response.raise_for_status()
            
            if destination:
                with open(destination, 'wb') as f:
                    f.write(response.content)
                return destination
            else:
                return response.content

    # ==================== Chat Management ====================

    async def getChatMember(self, user_id: int):
        """Chat a'zosi haqida ma'lumot"""
        return await self.bot.api_request("getChatMember", {
            "chat_id": self.chat_id,
            "user_id": user_id,
        })

    async def getChatAdministrators(self):
        """Chat administratorlari ro'yxati"""
        return await self.bot.api_request("getChatAdministrators", {
            "chat_id": self.chat_id,
        })

    async def getChatMemberCount(self):
        """Chat a'zolari soni"""
        return await self.bot.api_request("getChatMemberCount", {
            "chat_id": self.chat_id,
        })

    async def getChat(self):
        """Chat haqida ma'lumot"""
        return await self.bot.api_request("getChat", {
            "chat_id": self.chat_id,
        })

    async def leaveChat(self):
        """Chatdan chiqish"""
        return await self.bot.api_request("leaveChat", {
            "chat_id": self.chat_id,
        })

    async def banChatMember(self, user_id: int, **kwargs):
        """Foydalanuvchini bloklash"""
        params = {
            "chat_id": self.chat_id,
            "user_id": user_id,
            **kwargs
        }
        return await self.bot.api_request("banChatMember", params)

    async def unbanChatMember(self, user_id: int, **kwargs):
        """Foydalanuvchini blokdan chiqarish"""
        params = {
            "chat_id": self.chat_id,
            "user_id": user_id,
            **kwargs
        }
        return await self.bot.api_request("unbanChatMember", params)

    async def restrictChatMember(self, user_id: int, permissions: Dict, **kwargs):
        """Foydalanuvchi huquqlarini cheklash"""
        params = {
            "chat_id": self.chat_id,
            "user_id": user_id,
            "permissions": permissions,
            **kwargs
        }
        return await self.bot.api_request("restrictChatMember", params)

    async def promoteChatMember(self, user_id: int, **kwargs):
        """Foydalanuvchini admin qilish"""
        params = {
            "chat_id": self.chat_id,
            "user_id": user_id,
            **kwargs
        }
        return await self.bot.api_request("promoteChatMember", params)

    async def setChatTitle(self, title: str):
        """Chat nomini o'zgartirish"""
        return await self.bot.api_request("setChatTitle", {
            "chat_id": self.chat_id,
            "title": title,
        })

    async def setChatDescription(self, description: str):
        """Chat tavsifini o'zgartirish"""
        return await self.bot.api_request("setChatDescription", {
            "chat_id": self.chat_id,
            "description": description,
        })

    async def stopPoll(self, message_id: int, **kwargs):
        """Pollni to'xtatish"""
        params = {
            "chat_id": self.chat_id,
            "message_id": message_id,
            **kwargs
        }
        return await self.bot.api_request("stopPoll", params)