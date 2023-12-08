import discord
from discord.ext import commands
import data

intents = discord.Intents.default()
intents.message_content = True
client = commands.Bot(command_prefix='!', intents=intents)
TOKEN = open("../token", "r+").readline()


@client.event
async def on_ready():
    print("We have logged in as {0.user}".format(client))
    discord.Member = "@_CookieInside#2869"

@client.command(name="test")
async def test(ctx, args):
    await ctx.send("Du sagtest: " + args)

@client.command(name="addme")
async def add_me(ctx):
    data.add_player(ctx.user)

client.run(TOKEN)