import yt_dlp
from collections import deque
import discord
import asyncio

import asyncio
from collections import deque
import discord
import yt_dlp
import threading

class MusicPlayer:
    def __init__(self,  ydl_opts, connection=None, interaction=None):
        self.conn = connection
        self.ydl_opts = ydl_opts
        self.queue = deque()
        self.interaction = interaction
        self.loop = asyncio.get_event_loop()

    def remaining_songs(self):
        # returns the queue as a list
        return list(self.queue)

    async def setConnection(self, connection):
        self.conn = connection

    async def setInteraction(self, interaction):
        self.interaction = interaction

    def skipSong(self):
        if self.queue:
            self.conn.stop()
            asyncio.create_task(self.play_next())
            print(self.queue)

    async def add_to_queue(self, search_term):
        loop = asyncio.get_event_loop()
        with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
            info = await loop.run_in_executor(None, lambda: ydl.extract_info(search_term, download=False))
            url2 = info['entries'][0]['url']
            title = info['entries'][0]['title']
            self.queue.append((url2, title))

    async def unpause(self, error=None):
        if error:
            print(error)

        if self.queue:
            self.conn.resume()

    async def pause(self, error=None):
        if self.queue:
            self.conn.pause()

    def after(self, error):
        if error:
            print(f"Error in after callback: {error}")

        # Use stored reference to event loop to create task
        self.loop.call_soon_threadsafe(self.loop.create_task, self.play_next())

    async def play_next(self, error=None):
        try:
            print("play_next called")
            if error:
                print(f"Error in play_next: {error}")

            if self.queue:
                if self.conn.is_playing():
                    self.conn.stop()

                next_url, next_title = self.queue.popleft()
                source = discord.FFmpegPCMAudio(executable="/Users/joker/Documents/therapy_corner_bot/ffmpeg",
                                                source=next_url)

                self.conn.play(source, after=self.after)

                print(f"Playing: {next_title}")
                if self.interaction:
                    await self.interaction.channel.send(f"Now playing: {next_title}")

            else:
                print("Queue is empty.")

        except Exception as e:
            print(f"Exception in play_next: {e}")

    async def start(self):
        await self.play_next()

