from discord.ext import commands
import discord
from discord.ui import Button, View
import settings
from utils import send_log
import asyncio
import os
import traceback
from tickets import ticket_mod_role_id, closed_tickets_category_id, opened_tickets_category_id
from settings import TOKEN

status = discord.Status.dnd
activity=discord.CustomActivity(name='do “/request-a-bot” to request a FREE ai bot')

bot = commands.Bot(
    command_prefix=commands.when_mentioned_or("!"), 
    intents=discord.Intents.all(), 
    status=status,
    activity=activity
)

@bot.event
async def on_ready():
    print(f"running as {bot.user}")


class TrashButton(View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label="Delete this ticket", style=discord.ButtonStyle.red, emoji="🗑️", custom_id="trash")
    async def trash(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await interaction.channel.send("Deleting the ticket...")
        await asyncio.sleep(3)

        await interaction.channel.delete()

class CloseButton(View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label="Close the ticket", style=discord.ButtonStyle.red, custom_id="closeticket", emoji="🔒")
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)

        await interaction.channel.send("Closing this ticket...")

        await asyncio.sleep(3)

        category: discord.CategoryChannel = discord.utils.get(interaction.guild.categories, id=closed_tickets_category_id)

        r1: discord.Role = interaction.guild.get_role(ticket_mod_role_id)
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            r1: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_messages=True),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        }

        await interaction.channel.edit(category=category, overwrites=overwrites)
        await interaction.channel.send(
            embed=discord.Embed(
                title="Ticket Closed!",
                color=discord.Color.red()
            ),
            view=TrashButton()
        )

        # transcript = await get_transcript(
        #     member=interaction.user,
        #     channel=interaction.channel,
        #     token=settings.TOKEN
        # )

        await send_log(
            title="Ticket Closed",
            description=f"Closed by: {interaction.user.mention}",
            color=discord.Color.random(),
            guild=interaction.guild,
            # file=transcript
        )

        await asyncio.sleep(10)
        if os.path.exists('chat_exporter/ticket.html'):
            os.remove('chat_exporter/ticket.html')

class Feedback(discord.ui.Modal, title='Request a bot'):

    name = discord.ui.TextInput(
        label='Your bot\'s name',
        placeholder='Your bot\'s name here...',
        max_length=20
    )

    age = discord.ui.TextInput(
        label="Your character's age (must be 13+)",
        placeholder="Anything above 12 years old..."
    )

    history = discord.ui.TextInput(
        label="Your bot's history",
        placeholder="Who their parents are, family, etc.",
        style=discord.TextStyle.long,
        max_length=999
    )

    backstory = discord.ui.TextInput(
        label="What is your bot's backstory?",
        placeholder="More information about your AI Chatbot",
        style=discord.TextStyle.long,
        max_length=999
    )

    status = discord.ui.TextInput(
        label="Status and status type for your bot.",
        style=discord.TextStyle.long,
        placeholder='The text and status type.',
    )



    async def on_submit(self, interaction: discord.Interaction):
        category: discord.CategoryChannel = discord.utils.get(interaction.guild.categories, id=opened_tickets_category_id)
        for ch in category.text_channels:
            if ch.topic == f"{interaction.user.id} DO NOT CHANGE THE TOPIC OF THIS CHANNEL, IT WILL BREAK THINGS!":
                await interaction.response.send_message(f"You already have a ticket in {ch.mention}", ephemeral=True)
                return

        r1: discord.Role = interaction.guild.get_role(ticket_mod_role_id)
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            r1: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_messages=True),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            interaction.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_messages=True)
        }
        channel = await category.create_text_channel(
            name=f"{interaction.user}'s-ticket",
            topic=f"{interaction.user.id} DO NOT CHANGE THE TOPIC OF THIS CHANNEL, IT WILL BREAK THINGS!",
            overwrites=overwrites
        )

        await channel.send(f"<@{interaction.user.id}>, your ticket is ready!")
        await channel.send(f"<@&{ticket_mod_role_id}> will be with you soon.",
            embed=discord.Embed(
                title="Ticket Created!",
                description="Do not spam! You will get support soon.",
                color=discord.Color.green(),
            ),
            view=CloseButton()
        )
        await channel.send(
            embed=discord.Embed(
                title="Project Details",
                description=f"**Bot Name:** {self.name.value}\n**Bot Age:** {self.age.value}\n**Bot History:** {self.history.value}\n**Bot Backstory:** {self.backstory.value}\n**Bot Status:** {self.status.value}",
                color=discord.Color.blue()
            )
        )
        await interaction.response.send_message(
            embed=discord.Embed(
                description=f"Ticket created in {channel.mention}",
                color=discord.Color.random()
            ), 
            ephemeral=True
        )
        await send_log(title="Ticket Created",
            description=f"Created by {interaction.user.mention}",
            color=discord.Color.random(),
            guild=interaction.guild,
            # file=None
        )
    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        await interaction.response.send_message(f'Oops! Something went wrong. ``{error}``', ephemeral=True)

        traceback.print_exception(type(error), error, error.__traceback__)

@bot.tree.command(name="request-a-bot",description="Request a FREE AI Chatbot!")
async def request_a_bot(interaction: discord.Interaction):
    await interaction.response.send_modal(Feedback())

@bot.command(name="sync-tree")
@commands.is_owner()
async def sync_tree(ctx: commands.Context) -> None:
    msg: discord.Message = await ctx.reply("Syncing..")
    if ctx.author == ctx.bot.user:
        return
    ctx.bot.tree.copy_global_to(guild=ctx.bot.guilds[0])
    await ctx.bot.tree.sync()
    print("Tree loaded successfully")
    await msg.edit(content="Tree loaded successfully")

@bot.command(name="sync")
@commands.is_owner()
async def sync(ctx: commands.Context):
    msg: discord.Message = await ctx.reply("Syncing...")
    fmt = await ctx.bot.tree.sync(guild=ctx.guild)
    await msg.edit(content=f"Synced {len(fmt)} commands to the current guild.")

bot.run(TOKEN)
