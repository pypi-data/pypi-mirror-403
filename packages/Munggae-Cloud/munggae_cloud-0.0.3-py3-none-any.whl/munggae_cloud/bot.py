import discord, os, logging, aiohttp, traceback
from discord import Webhook
from discord.ext import commands

from .logging import setup_logging
from .Embed import Embed
from .watcher import FileWatcher

class MunggaeCloud(commands.Bot):
    def __init__(self, webhook_url: str = None, debug=False, *args, **kwargs):
        if "intents" not in kwargs:
            intents = discord.Intents.all()
            kwargs["intents"] = intents
        
        if debug:
            self.watcher = FileWatcher(self, dir_name="cogs")

        super().__init__(*args, **kwargs)
        setup_logging()
        self.logger = logging.getLogger("MunggaeCloud")
        self.webhook_url = webhook_url

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
            embed = Embed.error("오류 발생", "명령어 실행 중 알 수 없는 문제가 발생했습니다")
            await ctx.respond(embed=embed, ephemeral=True)

            if self.webhook_url:
                await self.send_error_webhook(ctx, error)
            
            self.logger.error(f"Command Error in '{ctx.command.name}': {error}")
    
    async def send_error_webhook(self, ctx, error):
        """에러 발생 시 디스코드 웹훅으로 리포트를 보냅니다"""
        async with aiohttp.ClientSession() as session:
            webhook = Webhook.from_url(self.webhook_url, session=session)
            
            tb = "".join(traceback.format_exception(type(error), error, error.__traceback__))
            if len(tb) > 4000: tb = tb[:4000] + "..."

            embed = discord.Embed(
                title=f"🚨 {self.user.name}봇 에러 발생!",
                description=f"**Command:** `/{ctx.command.name}`\n**User:** {ctx.author} ({ctx.author.id})",
                color=discord.Color.red()
            )
            embed.add_field(name="Traceback", value=f"```py\n{tb}\n```", inline=False)
            
            await webhook.send(embed=embed)
    
    def run(self, token: str, *args, **kwargs):
        """봇을 실행합니다"""
        try:
            super().run(token, *args, **kwargs)
        except discord.errors.PrivilegedIntentsRequired:
            self.logger.critical("🛑 [오류] 봇 실행 실패! (Privileged Intents Error)")
            self.logger.critical("👉 디스코드 개발자 포털(https://discord.com/developers)에서")
            self.logger.critical("   'Bot' 탭 -> 'Privileged Gateway Intents' 3개를 모두 켜주세요.")
        except discord.errors.LoginFailure:
            self.logger.critical("🛑 [오류] 토큰이 올바르지 않습니다. 다시 확인해주세요.")
        except Exception as e:
            self.logger.error(f"🛑 [오류] 알 수 없는 오류 발생: {e}")
            raise e