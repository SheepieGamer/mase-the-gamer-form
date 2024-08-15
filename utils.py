

import discord
from discord.ext import commands
import os
import settings
import tickets


async def send_log(title: str, guild: discord.Guild, description: str, color: discord.Color):
    log_channel = guild.get_channel(tickets.ticket_logs_channel_id)
    if not log_channel:
        return

    embed = discord.Embed(
        title=title,
        description=description,
        color=color
    )

    await log_channel.send(embed=embed)