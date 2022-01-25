import io
from typing import Optional

import discord
from redbot.core import commands

from .abc import MixinMeta
from .tts_api import generate_url
from .voices import voices


class BaseCommandsMixin(MixinMeta):
    @commands.command()
    @commands.cooldown(rate=1, per=3, type=discord.ext.commands.cooldowns.BucketType.user)
    @commands.guild_only()
    async def tts(self, ctx, file: Optional[bool] = False, *, text: str):
        """
        Plays the given text as TTS in your current voice channel.
        """
        if not file:
            if not ctx.author.voice or not ctx.author.voice.channel:
                await ctx.send("You are not connected to a voice channel.")
                return

            if ctx.guild.me.voice and ctx.guild.me.voice.channel:
                if ctx.author.voice.channel != ctx.guild.me.voice.channel:
                    await ctx.send("You are not in my voice channel.")
                    return
            else:
                current_perms = ctx.author.voice.channel.permissions_for(ctx.guild.me)
                if not current_perms.speak or not current_perms.connect:
                    await ctx.send(
                        "I do not have permissions to connect to and speak in this channel."
                    )
                    return

        author_data = await self.config.user(ctx.author).all()
        author_voice = author_data["voice"]
        author_translate = author_data["translate"]

        if author_voice not in voices.keys():
            await self.config.user(ctx.author).voice.clear()
            author_voice = await self.config.user(ctx.author).voice()

        text = self.decancer_text(text)

        if not text:
            await ctx.send("That's not a valid message, sorry.")
            return

        url = await generate_url(self, author_voice, text, author_translate)
        backup_url = await generate_url(self, "Anna", text, author_translate)

        if file:
            async with self.session.get(url) as resp:
                if resp.status != 200:
                    await ctx.send("Something went wrong. Try again later.")
                    return
                data = await resp.read()
                f = io.BytesIO(data)
                f.seek(0)
                await ctx.send(
                    content="Here's your TTS file!",
                    file=discord.File(fp=f, filename="tts.mp3"),
                )
                return

        track_info = ("Text to Speech", ctx.author)
        await self.play_sound(
            ctx.author.voice.channel,
            ctx.channel,
            "tts",
            [url, backup_url],
            track_info,
        )

    async def sfx_check(ctx):
        token = await ctx.bot.get_shared_api_tokens("freesound")
        if token.get("id") and token.get("key"):
            return True
        return False

    @commands.command()
    @commands.cooldown(rate=1, per=3, type=discord.ext.commands.cooldowns.BucketType.user)
    @commands.guild_only()
    @commands.check(sfx_check)
    async def sfx(self, ctx, file: Optional[bool] = False, *, sound: str):
        """
        Plays a sound effect in your current voice channel.

        Sounds are found on https://freesound.org
        """

        if not file:
            if not ctx.author.voice or not ctx.author.voice.channel:
                await ctx.send("You are not connected to a voice channel.")
                return

            if ctx.guild.me.voice and ctx.guild.me.voice.channel:
                if ctx.author.voice.channel != ctx.guild.me.voice.channel:
                    await ctx.send("You are not in my voice channel.")
                    return
            else:
                current_perms = ctx.author.voice.channel.permissions_for(ctx.guild.me)
                if not current_perms.speak or not current_perms.connect:
                    await ctx.send(
                        "I do not have permissions to connect to and speak in this channel."
                    )
                    return

        async with ctx.typing():

            async with self.session.get(
                "https://freesound.org/apiv2/search/text/",
                params={
                    "query": sound,
                    "token": self.key,
                    "filter": "duration:[0.5 TO 5]",
                },
            ) as resp:
                if resp.status != 200:
                    await ctx.send(
                        "Something went wrong when searching for the sound. Please try again later."
                    )
                    return

                data = await resp.json()
                results = data["results"]

                if not results:
                    await ctx.send("No sounds found for your query.")
                    return

                sound_id = results[0]["id"]

            async with self.session.get(
                f"https://freesound.org/apiv2/sounds/{sound_id}/",
                params={"token": self.key},
            ) as resp:
                if resp.status != 200:
                    await ctx.send(
                        "Something went wrong when getting the sound. Please try again later."
                    )
                    return

                data = await resp.json()
                url = data["previews"]["preview-hq-mp3"]
                track_info = (data["description"], ctx.author)

            if file:
                async with self.session.get(url) as resp:
                    if resp.status != 200:
                        await ctx.send("Something went wrong. Try again later.")
                        return
                    file_data = await resp.read()
                    f = io.BytesIO(file_data)
                    f.seek(0)
                    await ctx.send(
                        content=f"Here's '{data['description']}'",
                        file=discord.File(fp=f, filename=f"{data['description']}.mp3"),
                    )
                    return

            await self.play_sound(
                ctx.author.voice.channel,
                ctx.channel,
                "sfx",
                [url],
                track_info,
            )
