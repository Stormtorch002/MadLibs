from database import db as db_file
from discord.ext import commands
from config import TOKEN, PASTEBIN_API_KEY
import discord
from aiohttp import ClientSession
import asyncio
import json
import re


def case(prefix):
    return [
        prefix,
        prefix.upper(),
        prefix.lower(),
        prefix.capitalize()
    ]


async def get_prefixes():
    d = await db_file.create_tables()
    query = 'SELECT guild_id, prefix FROM prefixes'
    return {res['guild_id']: res['prefix'] for res in await d.fetch(query)}, d


prefixes, db = asyncio.get_event_loop().run_until_complete(get_prefixes())


def get_prefix(client, message):
    prefix = prefixes.get(message.guild.id)
    return case(prefix) if prefix else ['ml!', 'ML!', 'Ml!']


cogs = (
    'cogs.listeners',
    'cogs.madlibs',
    'cogs.config',
    'jishaku'
)
bot = commands.Bot(
    command_prefix=get_prefix,
    case_insensitive=True,
    activity=discord.Game('ml!help')
)
bot.remove_command('help')
bot.db = db
bot.prefixes = prefixes
bot.finder = re.compile('{(.+?)}')

with open('./defaults.json') as f:
    bot.lengths = {}
    bot.defaults = json.load(f)
    bot.templates = {}
    bot.names = {}
    count = 1

    for default in bot.defaults:
        length = len(bot.finder.findall(bot.defaults[default]))
        bot.lengths[default] = length
        bot.templates[count] = bot.defaults[default]
        bot.names[count] = default
        count += 1

[bot.load_extension(cog) for cog in cogs]

ICON = 'https://media.discordapp.net/attachments/742973400636588056/745710912257916950/159607234227809532.png'
INVITE = 'https://discord.com/oauth2/authorize?client_id=742921922370600991&permissions=19521&scope=bot'
GITHUB = 'https://github.com/Stormtorch002/MadLibs'


@bot.command()
@commands.cooldown(2, 60, commands.BucketType.user)
async def feedback(ctx, *, user_feedback):
    embed = discord.Embed(
        title='New Feedback!',
        description=f'`{user_feedback}`',
        color=ctx.author.color
    )
    embed.set_author(name=str(ctx.author), icon_url=str(ctx.author.avatar_url_as(format='png')))
    embed.set_footer(text=f'Guild ID: {ctx.guild.id}')
    await bot.get_user(553058885418876928).send(embed=embed)
    await ctx.send(':thumbsup: Your feedback has been sent!')


@feedback.error
async def feedback_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f'You can only give feedback twice per hour. Please wait another '
                       f'`{error.retry_after:.2f}` seconds.')


@bot.command()
async def invite(ctx):
    await ctx.send(f'**You can invite me here:**\n'
                   f'<https://discord.com/oauth2/authorize?client_id=742921922370600991&permissions=19521&scope=bot>')


@bot.command()
async def pastebin(ctx, *, text):
    data = {
        'api_dev_key': PASTEBIN_API_KEY,
        'api_option': 'paste',
        'api_paste_code': text,
        'api_paste_name': f"{ctx.author}'s Paste"
    }
    async with ClientSession() as session:
        async with session.post('https://pastebin.com/api/api_post.php', data=data) as resp:
            await ctx.send(await resp.text())


@bot.command(name='help', aliases=['cmds', 'commands'])
async def _help(ctx):
    if not ctx.channel.permissions_for(ctx.guild.me).embed_links:
        return await ctx.send('I need the `Embed Links` permission to display help.')

    embed = discord.Embed(color=discord.Colour.blue())
    embed.title = f'Commands'
    embed.set_thumbnail(url=ICON)
    embed.description = f'[`Source Code`]({GITHUB})\n[**Invite Me!**]({INVITE})'
    p = ctx.prefix.lower()

    cmds = {
        f"{p}**prefix**": 'Shows/changes the current server prefix',
        f"{p}**invite**": 'Sends my invite link!',
        f"{p}**madlibs**": 'Lets you host a MadLibs game',
        f"{p}**plays**": "Gets a play from the history of the server's laughable moments",
        f"{p}**custom**": 'Manages custom story templates for the current server',
        f"{p}**feedback**": "Gives feedback about anything related to the bot, including source code",
        f"{p}**pastebin**": "Not really relevant but creates a pastebin paste and sends you the URL.",
    }

    [embed.add_field(name=cmd, value=cmds[cmd], inline=False) for cmd in cmds]
    await ctx.send(embed=embed)


if __name__ == '__main__':
    bot.run(TOKEN)
