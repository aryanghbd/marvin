import asyncio
import random

import discord
from discord.ext import commands, tasks
from discord import Intents
import requests
from requests.auth import HTTPBasicAuth

TOKEN = "MTA0NjA0ODM0NDE5MzExNDE3Mw.G2tyzb.9-_Dh8HC2QapyTV15A-ZkNxxqVq9UKO6fpDys8"

headers = {'Accept': 'application/json'}
auth = HTTPBasicAuth('apikey', '0WFG_xWfBhcTawJFiLVm5AeF')
quoteurl = "https://quotes.rest/qod"

client = commands.Bot(command_prefix='$', intents = Intents.all())
filimemeo = False
in_prog = False

helper_questions = ["Are you comfortable with triggering topics?", "Are you willing to stay active in order to help people as a councillor?", "Are you aware of most mental disorders?", "Do you have experience with counselling people?", "Are you at least a little familiar to the psychology field?", "Are you able to handle stress/anxiety well?",
                    "Are you able to keep a positive mood at all times?", "Would you consider your feelings being more important than the person you are and will be helping?", "Do you know any methods to help people who have trauma?",
                    "Do you track mental health data and is it important to you?"]



@client.event
async def on_ready():
    print('connected to discord!')
    channel = client.get_channel(1045823574084169738)
    await channel.send("i am a bot and do not care for your emotions, erika is a hot mommy, test successful")
    await regular_riddle.start()

@client.event
async def on_message(message):
    # //if "erika" in message.content:
    #     await message.channel.send("is a hot mommy")
    if message.author.id == 906212102757294080 and filimemeo is True:
        await message.add_reaction('🇵🇭')
        await client.process_commands(message)
    else:
        await client.process_commands(message)



# @tasks.loop(hours=24)
# async def quote_of_the_day():
#     quoteChannel = client.get_channel(1041717466633605130)
#     response = requests.get("https://quotes.rest/qod").json()
#     quote = response['quotes']['quote']
#     print(quote)


@tasks.loop(hours = 2)
async def regular_riddle():
    riddleChannel = client.get_channel(1041718370564849775)
    response = requests.get("https://riddles-api.vercel.app/random").json()
    await client.get_user(623602247921565747).send(response['answer'])
    await riddleChannel.send(response['riddle'])

@client.command()
async def test(ctx):
    print("test of test")
    await ctx.channel.send("test")


@client.command()
async def getQuote(ctx):
    response = requests.get(quoteurl, headers=headers, auth=auth).json()
    print(response)

# @client.command()
# async def getRiddle(ctx):
#     response = requests.get("https://riddles-api.vercel.app/random").json()
#     await client.get_user(623602247921565747).send(response['answer'])
#     print(response['riddle'])

@client.command()
async def emergency(ctx):

    region = None
    hotlines = {}

    european_role = discord.utils.get(ctx.guild.roles, name = "Europe")
    na_role = discord.utils.get(ctx.guild.roles, name = "Noth America")
    asia_role = discord.utils.get(ctx.guild.roles, name = "Asia")
    await ctx.channel.send("Remember, you are loved. The following numbers have been pooled for your region, all numbers are free of charge to use. Many of these services operate on a 24/7 basis unless stated otherwise. It is urgently recommended that in the event of a medical emergency to call your national emergency service number immediately, be aware that certain services may intervene and contact emergency services if you are in immediate medical danger.")

    if european_role in ctx.author.roles:
        region = "Europe"
        hotlines = ["Samaritans: 116 123 by Phone (UK)", "National Suicide Prevention Helpline UK: 0800 689 5652 by Phone", "France: National Suicide Hotline - 3114 by Phone", "Germany: 116 123 for German Samaritans", "Spain: Suicide Crisis Line - 024 by Phone"]

    elif na_role in ctx.author.roles:
        region = "North America"
        hotlines = ["US: 211 for emergency referrals to social services", "US: 988 Suicide and Crisis hotline, 24/7", "US: Crisis intervention text-service - text 'HOME' to 741 741", "Canada: Crisis Text Line - HOME (for English services), PARLER (for French services) to 686868", "Canada: Talk Suicide Canada - 45645 (24/7) service"]

    elif asia_role in ctx.author.roles:
        region = "Asia"
        hotlines = ["China: Beijing Suicide Research and Prevention Center: 800-810-1117, available 24/7", "China: Lifeline China 400-821-1215", "Hong Kong: Samaritans HK: 2896 0000.", "Korea: Lifeline Korea - 1588-9191", "Malaysia: MIASA - 1-800-820066", "Philipines: National Center for Mental Health 24/7 Crisis Hotline: (02) 7989-USAP (8727) or 0917 899 USAP (8727)"]

    em = discord.Embed(title="Emergency Hotlines for " + region, color=discord.Color.from_rgb(30, 74, 213))
    em.add_field(name="Question: ", value=hotlines)
    await ctx.channel.send(embed=em)


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

    global in_prog
    if in_prog is True:
        await ctx.send("Please wait for the current councillor test to conclude")

    else:
        in_prog = True
        em = discord.Embed(title="Your Councillor Application", color=discord.Color.from_rgb(30, 74, 213))
        em.add_field(name="Councillor Test Information", value=ctx.author.name + ", thank you for considering joining the Councillor team! Please proceed to #councillor-test-" + ctx.author.name + " for an evaluation to see if you are a fit!")
        await ctx.send(embed=em)

        user = ctx.message.author
        testrole = discord.utils.get(user.guild.roles, name="councillor test candidate")
        await user.add_roles(testrole)

        guild = ctx.message.guild
        c = discord.utils.get(guild.categories, name = "councillors")
        test_channel = await guild.create_text_channel('councillor test ' + ctx.author.name, category=c)

        questionpool = random.sample(helper_questions, 5)
        answers = 0

        for question in questionpool:
            em = discord.Embed(title="Helper Quiz", color=discord.Color.from_rgb(30, 74, 213))
            em.add_field(name="Question: ", value=question)
            msg = await test_channel.send(embed=em)
            await msg.add_reaction('\u2705')
            await msg.add_reaction('\u274c')

            while True:
                try:
                    reaction = await client.wait_for("reaction_add", timeout=120)

                    if str(reaction[0]) == '✅':
                        print("test")

                    answers = answers + 1 if str(reaction[0]) == '\u2705' else answers
                    print(answers)
                    print(reaction[0])
                    print(reaction)

                    break

                except asyncio.TimeoutError:
                    print("Too slow, loser")

        if answers >= 3:
            msg = await test_channel.send("Congratulations! You seem to display all the right characteristics to be a great councillor on our server, we have given you the Councillor role, remember that with great power comes with great responsibility! If you are ready to start helping, please react with a tick to this message to acknowledge that this role is dependent on consistently good positive server behaviour, and breaching such conditions is subject to you losing this role.")
            await msg.add_reaction('\u2705')
            while True:
                try:
                    reaction = await client.wait_for("reaction_add", timeout=120)

                    if str(reaction[0]) == '\u2705':
                        user = ctx.message.author
                        role = discord.utils.get(user.guild.roles, name = "councillor")
                        await user.add_roles(role)
                        await user.remove_roles(testrole)
                        await test_channel.delete()

                    break

                except asyncio.TimeoutError:
                    print("Too slow, loser")

        else:
            await test_channel.send("You have the mental health knowledge of a self diagnoser")
            await asyncio.wait(10)
            await user.remove_roles(testrole)
            test_channel.delete()

    in_prog = False

@regular_riddle.before_loop
async def before():
    await client.wait_until_ready()
    print("Finished waiting")

client.run(TOKEN)