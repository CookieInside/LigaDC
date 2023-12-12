import discord
from discord.ui import Select, View
from discord.ext import commands
import data

intents = discord.Intents.default()
intents.message_content = True
client = commands.Bot(command_prefix='!', intents=intents)
TOKEN = open("token", "r+").readline()

@client.event
async def on_ready():
    print("We have logged in as {0.user}".format(client))
    discord.Member = "@_CookieInside#2869"

@client.command(name="test")
async def test(ctx, args):
    await ctx.send("Du sagtest: " + args)

@client.command(name="addme")
async def add_me(ctx):
    data.add_player(f"<@{ctx.author.id}>")
    await ctx.send(f"User <@{ctx.author.id}> was added successfully!")

@client.command(name="bet")
async def bet(ctx):
    data.load_season()
    matches = data.get_bet_matches_info()
    matches.sort(key=lambda match: int(match[3]))
    options = []
    for i in range(len(matches)):
        match_string = f"{matches[i][0]} gegen {matches[i][1]} in {matches[i][3]} Tagen"
        options.append(discord.SelectOption(label=match_string, value=str(i)))
    class Match_select(View):
        @discord.ui.select(
            placeholder="Wähle ein Spiel:",
            options=options
        )
        async def select_callback(self, select, interaction):
            for i in range(len(options)):
                if select.values[0] == str(i):
                    await interaction.response.edit_message(content=f"Du hast Spiel Nr.{i} ausgewählt.")
    await ctx.send(view=Match_select())
client.run(TOKEN)