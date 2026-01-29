from typing import Callable
import re


class Filter:
    """
    Custom filter yaratish uchun
    
    Example:
        is_admin = Filter(lambda ctx: ctx.from_user.id in ADMIN_IDS)
        
        @bot.filter(is_admin)
        async def admin_handler(ctx):
            await ctx.reply("Admin paneliga xush kelibsiz!")
    """
    
    def __init__(self, predicate: Callable):
        self.predicate = predicate
    
    def __call__(self, ctx):
        return self.predicate(ctx)
    
    def __and__(self, other):
        """AND operator"""
        return Filter(lambda ctx: self(ctx) and other(ctx))
    
    def __or__(self, other):
        """OR operator"""
        return Filter(lambda ctx: self(ctx) or other(ctx))
    
    def __invert__(self):
        """NOT operator"""
        return Filter(lambda ctx: not self(ctx))


# Tayyor filtrlar
class Filters:
    """Tayyor filtrlar to'plami"""
    
    @staticmethod
    def text(ctx):
        """Matn xabar"""
        return ctx.message and ctx.message.text is not None
    
    @staticmethod
    def photo(ctx):
        """Rasm xabar"""
        return ctx.message and ctx.message.photo is not None
    
    @staticmethod
    def video(ctx):
        """Video xabar"""
        return ctx.message and ctx.message.video is not None
    
    @staticmethod
    def audio(ctx):
        """Audio xabar"""
        return ctx.message and ctx.message.audio is not None
    
    @staticmethod
    def voice(ctx):
        """Voice xabar"""
        return ctx.message and ctx.message.voice is not None
    
    @staticmethod
    def video_note(ctx):
        """Video note xabar"""
        return ctx.message and ctx.message.video_note is not None
    
    @staticmethod
    def document(ctx):
        """Document xabar"""
        return ctx.message and ctx.message.document is not None
    
    @staticmethod
    def animation(ctx):
        """Animation (GIF) xabar"""
        return ctx.message and ctx.message.animation is not None
    
    @staticmethod
    def sticker(ctx):
        """Sticker xabar"""
        return ctx.message and ctx.message.sticker is not None
    
    @staticmethod
    def location(ctx):
        """Location xabar"""
        return ctx.message and ctx.message.location is not None
    
    @staticmethod
    def venue(ctx):
        """Venue xabar"""
        return ctx.message and ctx.message.venue is not None
    
    @staticmethod
    def contact(ctx):
        """Contact xabar"""
        return ctx.message and ctx.message.contact is not None
    
    @staticmethod
    def poll(ctx):
        """Poll xabar"""
        return ctx.message and ctx.message.poll is not None
    
    @staticmethod
    def dice(ctx):
        """Dice xabar"""
        return ctx.message and ctx.message.dice is not None
    
    @staticmethod
    def private_chat(ctx):
        """Shaxsiy chat"""
        return ctx.chat and ctx.chat.type == "private"
    
    @staticmethod
    def group_chat(ctx):
        """Guruh chat"""
        return ctx.chat and ctx.chat.type in ["group", "supergroup"]
    
    @staticmethod
    def channel(ctx):
        """Kanal"""
        return ctx.chat and ctx.chat.type == "channel"
    
    @staticmethod
    def forwarded(ctx):
        """Forward qilingan xabar"""
        return ctx.message and (ctx.message.forward_from is not None or ctx.message.forward_from_chat is not None)
    
    @staticmethod
    def reply(ctx):
        """Reply qilingan xabar"""
        return ctx.message and ctx.message.reply_to_message is not None
    
    @staticmethod
    def has_media(ctx):
        """Biror media bor"""
        if not ctx.message:
            return False
        return any([
            ctx.message.photo,
            ctx.message.video,
            ctx.message.audio,
            ctx.message.voice,
            ctx.message.video_note,
            ctx.message.document,
            ctx.message.animation,
            ctx.message.sticker,
        ])
    
    @staticmethod
    def regex(pattern: str, flags: int = 0):
        """Regex filter
        
        Example:
            @bot.filter(Filters.regex(r'^/start'))
            async def start(ctx):
                await ctx.reply("Start!")
        """
        compiled = re.compile(pattern, flags)
        
        def filter_func(ctx):
            if ctx.message and ctx.message.text:
                return compiled.search(ctx.message.text) is not None
            return False
        
        return Filter(filter_func)
    
    @staticmethod
    def user_id(*user_ids: int):
        """Foydalanuvchi ID filtri
        
        Example:
            @bot.filter(Filters.user_id(123456, 789012))
            async def admin_handler(ctx):
                await ctx.reply("Admin!")
        """
        def filter_func(ctx):
            return ctx.from_user and ctx.from_user.id in user_ids
        
        return Filter(filter_func)
    
    @staticmethod
    def chat_id(*chat_ids: int):
        """Chat ID filtri
        
        Example:
            @bot.filter(Filters.chat_id(-100123456789))
            async def specific_chat_handler(ctx):
                await ctx.reply("Bu maxsus chat!")
        """
        def filter_func(ctx):
            return ctx.chat and ctx.chat.id in chat_ids
        
        return Filter(filter_func)
    
    @staticmethod
    def file_extension(*extensions: str):
        """Fayl kengaytmasi filtri
        
        Example:
            @bot.filter(Filters.file_extension('pdf', 'docx'))
            async def document_handler(ctx):
                await ctx.reply("PDF yoki DOCX fayl qabul qilindi!")
        """
        normalized_extensions = [ext.lower().lstrip('.') for ext in extensions]
        
        def filter_func(ctx):
            if not ctx.message:
                return False
            
            filename = None
            if ctx.message.document:
                filename = ctx.message.document.file_name
            elif ctx.message.audio:
                filename = ctx.message.audio.file_name
            elif ctx.message.video:
                filename = ctx.message.video.file_name
            
            if filename:
                file_ext = filename.split('.')[-1].lower() if '.' in filename else ''
                return file_ext in normalized_extensions
            
            return False
        
        return Filter(filter_func)
    
    @staticmethod
    def caption_regex(pattern: str, flags: int = 0):
        """Caption regex filtri
        
        Example:
            @bot.filter(Filters.caption_regex(r'important'))
            async def important_media(ctx):
                await ctx.reply("Muhim media!")
        """
        compiled = re.compile(pattern, flags)
        
        def filter_func(ctx):
            if ctx.message and ctx.message.caption:
                return compiled.search(ctx.message.caption) is not None
            return False
        
        return Filter(filter_func)
    
    @staticmethod
    def command(*commands: str):
        """Command filtri
        
        Example:
            @bot.filter(Filters.command('start', 'help'))
            async def commands_handler(ctx):
                await ctx.reply("Start yoki Help!")
        """
        def filter_func(ctx):
            if ctx.message and ctx.message.text:
                text = ctx.message.text
                if text.startswith('/'):
                    cmd = text.split()[0][1:].split('@')[0]
                    return cmd in commands
            return False
        
        return Filter(filter_func)