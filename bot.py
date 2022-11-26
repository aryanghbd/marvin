import asyncio
import random

import discord
from discord.ext import commands
from discord import Intents
TOKEN = "MTA0NjA0ODM0NDE5MzExNDE3Mw.G2tyzb.9-_Dh8HC2QapyTV15A-ZkNxxqVq9UKO6fpDys8"


client = commands.Bot(command_prefix='$', intents = Intents.all())
filimemeo = False

helper_questions = ["Are you comfortable with triggering topics?", "Are you willing to stay active in order to help people as a councillor?", "Are you aware of most mental disorders?", "Do you have experience with counselling people?", "Are you at least a little familiar to the psychology field?", "Are you able to handle stress/anxiety well?"]



@client.event
async def on_ready():
    print('connected to discord!')
    channel = client.get_channel(1045823574084169738)
    await channel.send("i am a bot and do not care for your emotions, erika is a hot mommy, test successful")

@client.event
async def on_message(message):
    # //if "erika" in message.content:
    #     await message.channel.send("is a hot mommy")
    if message.author.id == 906212102757294080 and filimemeo is True:
        await message.add_reaction('🇵🇭')
        await client.process_commands(message)
    else:
        await client.process_commands(message)


@client.command()
async def test(ctx):
    print("test of test")
    await ctx.channel.send("test")

@client.command()
async def toggle_poof_xenophobia(ctx):
    global filimemeo
    if filimemeo is False and ctx.author.id == 623602247921565747 :
        filimemeo = True
        await ctx.send("Poof xenophobia set to ON")
    else:
        if ctx.author.id == 623602247921565747:
            filimemeo = False
            await ctx.send("I feel like a nice bot today, I will stop being xenophobic to Poof now")
        else:
            await ctx.send("Only my creator is allowed to use this command")

@client.command()
async def applycouncillor(ctx):
    em = discord.Embed(title="rich embed test", color=discord.Color.from_rgb(30, 74, 213))
    em.add_field(name="test", value="god damn")
    await ctx.send(embed=em)

    guild = ctx.message.guild
    c = discord.utils.get(guild.categories, name = "staff")
    test_channel = await guild.create_text_channel('councillor test ' + ctx.author.name, category=c)

    questionpool = random.sample(helper_questions, 3)
    answers = 0

    for question in questionpool:
        em = discord.Embed(title="Helper Quiz", color=discord.Color.from_rgb(30, 74, 213))
        em.add_field(name="Question: ", value=question)
        msg = await test_channel.send(embed=em)
        await msg.add_reaction('✅')
        await msg.add_reaction('❌')

        while True:
            try:
                reaction = await client.wait_for("reaction_add", timeout=120)

                await msg.remove_reaction(reaction, ctx.author)

            except asyncio.TimeoutError:
                print("Too slow, loser")
    await test_channel.send("i am here now my nigga")



client.run(TOKEN)