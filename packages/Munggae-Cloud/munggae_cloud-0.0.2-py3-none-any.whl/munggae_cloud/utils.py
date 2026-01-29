import discord, time
from discord.ext import commands
from discord.utils import MISSING
from typing import Union, Optional
from datetime import datetime

async def response(
    ctx: Union[discord.ApplicationContext, commands.Context, discord.Interaction],
    content: Optional[str] = MISSING,
    embed: discord.Embed = MISSING,
    **kwargs
):
    """
    상황에 맞춰 respond, followup.send, reply, send 중 적절한 메소드를 자동으로 선택하여 응답합니다
    """
    func = None
    
    if isinstance(ctx, (discord.ApplicationContext, discord.Interaction)) or hasattr(ctx, 'interaction'):
        interaction = getattr(ctx, 'interaction', ctx)
        if interaction.response.is_done():
            func = interaction.followup.send
        else:
            func = ctx.respond if hasattr(ctx, 'respond') else interaction.response.send_message
    else:
        func = ctx.reply if hasattr(ctx, 'reply') else ctx.send

    if content is not MISSING:
        kwargs['content'] = content
    if embed is not MISSING:
        kwargs['embed'] = embed

    return await func(**kwargs)

def to_timestamp(date_time: datetime, style: str = "R") -> str:
    """
    datetime 객체를 디스코드 타임스탬프 문자열로 변환합니다
    style: R(상대시간), d(짧은날짜), D(긴날짜), t(짧은시간), T(긴시간), f(전체), F(요일포함전체)
    """
    ts = int(date_time.timestamp())
    return f"<t:{ts}:{style}>"

def current_time(style: str = "f") -> str:
    """현재 시간을 디스코드 타임스탬프로 반환합니다"""
    ts = int(time.time())
    return f"<t:{ts}:{style}>"