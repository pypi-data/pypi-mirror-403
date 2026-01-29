import discord, os, logging
from discord.ext import commands

from .logging import setup_logging
from .Embed import Embed

class MunggaeCloud(discord.Bot):
    def __init__(self, description=None, *args, **kwargs):
        super().__init__(description=description, *args, **kwargs)
        setup_logging()
        self.logger = logging.getLogger("MunggaeCloud")

    def load_cogs(self, dir_name: str = "cogs"):
        """Cog 자동 로드 함수"""
        if not os.path.exists(dir_name):
            self.logger.warning(f"⚠️  '{dir_name}' 폴더가 없습니다.")
            return

        count = 0
        for root, dirs, files in os.walk(dir_name):
            for file in files:
                if file.endswith(".py") and not file.startswith("_"):
                    path = os.path.join(root, file)
                    module_name = path.replace(os.sep, ".")[:-3]
                    try:
                        self.load_extension(module_name)
                        self.logger.info(f"🧩 Loaded Extension: {module_name}")
                        count += 1
                    except Exception as e:
                        self.logger.error(f"🚫 Failed to load {module_name}: {e}")
        
        print(f"\n✨ {count} Cogs Loaded Successfully.\n")

    async def on_ready(self):
        print("-" * 30)
        self.logger.info(f"🚀 {self.user.name} is Online! (ID: {self.user.id})")
        self.logger.info(f"☁️  Powered by Munggae-Cloud Library")
        print("-" * 30)

    async def on_application_command_error(self, ctx: discord.ApplicationContext, error: discord.DiscordException):
        if getattr(ctx, "handled", False):
            return

        if isinstance(error, commands.CommandOnCooldown):
            seconds = round(error.retry_after, 2)
            embed = Embed.warning("잠시만요!", f"⏳ **{seconds}초** 뒤에 다시 시도해주세요.")
            await ctx.respond(embed=embed, ephemeral=True)

        elif isinstance(error, commands.MissingPermissions):
            perms = ", ".join(error.missing_permissions)
            embed = Embed.error("권한 부족", f"이 명령어를 쓰려면 **{perms}** 권한이 필요합니다.")
            await ctx.respond(embed=embed, ephemeral=True)

        elif isinstance(error, commands.BotMissingPermissions):
            perms = ", ".join(error.missing_permissions)
            embed = Embed.error("봇 권한 부족", f"제가 이 작업을 하려면 **{perms}** 권한이 필요해요.")
            await ctx.respond(embed=embed, ephemeral=True)

        else:
            embed = Embed.error("오류 발생", "명령어 실행 중 알 수 없는 문제가 발생했습니다.")
            await ctx.respond(embed=embed, ephemeral=True)
            
            self.logger.error(f"Command Error in '{ctx.command.name}': {error}")