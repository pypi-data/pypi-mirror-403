import discord

class Embed(discord.Embed):
    """기본 discord.Embed를 확장하여 자주 쓰는 스타일을 제공합니다"""
    
    def __init__(self, *args, **kwargs):
        if "color" not in kwargs:
            kwargs["color"] = 0x5865F2 
        super().__init__(*args, **kwargs)

    @classmethod
    def success(cls, title, description):
        return cls(title=f"✅ {title}", description=description, color=discord.Color.green())

    @classmethod
    def error(cls, title, description):
        return cls(title=f"❌ {title}", description=description, color=discord.Color.red())
    
    @classmethod
    def warning(cls, title, description):
        return cls(title=f"⚠️ {title}", description=description, color=discord.Color.gold())