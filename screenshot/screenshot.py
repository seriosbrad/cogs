from redbot.core import commands, Config, checks
from pyppeteer import launch
import pyppeteer
import discord
import asyncio
import io


class Screenshot(commands.Cog):
    """Screenshots a given link."""

    @commands.bot_has_permissions(attach_files=True)
    @commands.command(aliases="ss")
    @commands.is_owner()
    async def screenshot(self, ctx, link: str, wait: int = 0):
        """Screenshots a given link."""

        await ctx.trigger_typing()
        browser = await launch()
        page = await browser.newPage()
        try:
            await page.goto(link)
        except pyppeteer.page.PageError:
            await ctx.send("Sorry, I couldn't find anything at that link!")
            await browser.close()
            return
        except Exception:
            await ctx.send(
                "Sorry, I ran into an issue! Make sure to include http:// or https:// at the beginning of the link."
            )
            await browser.close()
            return

        await asyncio.sleep(wait)
        result = await page.screenshot()
        await browser.close()
        f = io.BytesIO(result)
        file = discord.File(f, filename="screenshot.png")
        await ctx.send(file=file)
