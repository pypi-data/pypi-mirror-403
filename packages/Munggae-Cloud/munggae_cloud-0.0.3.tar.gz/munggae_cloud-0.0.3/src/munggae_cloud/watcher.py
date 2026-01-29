import os
import asyncio
import logging
from discord.ext import tasks

class FileWatcher:
    def __init__(self, bot, dir_name="cogs"):
        self.bot = bot
        self.dir_name = dir_name
        self.last_modified = {}
        self.logger = logging.getLogger("FileWatcher")
        
        self.scan_files()
        self.watch_loop.start()

    def scan_files(self):
        """현재 파일들의 수정 시간을 기록합니다"""
        for root, _, files in os.walk(self.dir_name):
            for file in files:
                if file.endswith(".py"):
                    path = os.path.join(root, file)
                    self.last_modified[path] = os.stat(path).st_mtime

    @tasks.loop(seconds=1)
    async def watch_loop(self):
        """1초마다 파일 변경을 감지합니다"""
        for root, _, files in os.walk(self.dir_name):
            for file in files:
                if file.endswith(".py"):
                    path = os.path.join(root, file)
                    try:
                        mtime = os.stat(path).st_mtime
                    except FileNotFoundError:
                        continue

                    if path in self.last_modified and mtime > self.last_modified[path]:
                        self.last_modified[path] = mtime
                        await self.reload_cog(path)

    async def reload_cog(self, path):
        module_name = path.replace(os.sep, ".")[:-3]
        try:
            self.bot.reload_extension(module_name)
            self.logger.info(f"🔄 Detected change in {module_name}, Reloaded!")
        except Exception as e:
            self.logger.error(f"🚫 Failed to reload {module_name}: {e}")