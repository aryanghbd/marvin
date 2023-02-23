import asyncio
import random

import discord
from discord.ext import commands, tasks
from discord import Intents
from discord import app_commands
import requests
import pymongo
from pymongo import MongoClient
import time
import datetime
import openai
from requests.auth import HTTPBasicAuth

TOKEN = "MTA0NjA0ODM0NDE5MzExNDE3Mw.GOLvSP.gqnjFwo3wsUwgNaK_ptSO0fgNNt1Sz7NNH7Tbg"

url = "https://discord.com/api/v10/applications/1046048344193114173/commands"

client = commands.Bot(command_prefix='$', intents = Intents.all())
cluster = MongoClient("mongodb+srv://tcadmin:erikamommy123@cluster0.9wobd.mongodb.net/test")
db = cluster["UserData"]
collection = db["SoberJournies"]

openai.api_key = "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"

filimemeo = False
in_prog = False
answer = ""
import openai

openai.api_key = "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"

substring = "-gpt"
def generate_response(prompt):
    completions = openai.Completion.create(
        engine="text-davinci-003",
        prompt=f"User: {prompt}\nChatGPT: ",
        max_tokens=1024,
        n=1,
        stop=None,
        temperature=0.5,
    )

    message = completions.choices[0].text
    return message.strip()


helper_questions = ["Are you comfortable with triggering topics?", "Are you willing to stay active in order to help people as a councillor?", "Are you aware of most mental disorders?", "Do you have experience with counselling people?", "Are you at least a little familiar to the psychology field?", "Are you able to handle stress/anxiety well?",
                    "Are you able to keep a positive mood at all times?", "Would you consider your feelings being more important than the person you are and will be helping?", "Do you know any methods to help people who have trauma?",
                    "Do you track mental health data and is it important to you?"]

@client.tree.command(name = "askgpt", description="Ask a question and get an AI response!")
async def askgpt(interaction, question : str):
    resp = (generate_response(question))
    if substring in resp:
        await interaction.response.send_message("You thought you were slick with that recursive loop, didn't you")
    else:
        await interaction.user.send(str(resp))
        await interaction.response.send_message("Please check your DMs for a response to your anonymous question.")


@client.tree.command(name = "revealriddleanswer", description = "Reveal the answer to the Riddle") #Add the guild ids in which the slash command will appear. If it should be in all, remove the argument, but note that it will take some time (up to an hour) to register the command if it's for all guilds.
async def riddleanswer(interaction):
    await interaction.response.send_message("Damn you must suck at riddles, L bozo. The answer to the current riddle is: " + answer)

@client.tree.command(name = "startsoberjourney", description = "Every journey begins with a single step")
async def startSoberJourney(interaction, journey : str):
    collection.insert_one({"_id" : interaction.user.id, "_journey" : journey, "_since" : datetime.datetime.now()})
    await interaction.response.send_message("Journey recorded! Good luck!")

@client.tree.command(name = "viewsoberjourney", description = "Reflect on your progress so far")
async def viewSoberJourney(interaction):
    try:
        entry = collection.find_one({"_id" : interaction.user.id})
        journey = entry.get("_journey")
        journeyStart = entry.get("_since")

        diff = (datetime.datetime.now() - journeyStart)
        days = diff.days
        weeks, rem = divmod(days, 7)
        hours, remainder = divmod(diff.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        username = str(client.get_user(interaction.user.id))
        message = "You have been clean from " + journey + " for %d weeks, %d days, %d hours and %d minutes now! Great job!" % (weeks, days, hours, minutes)

        em = discord.Embed(title= username + "'s Sober Journey", color=discord.Color.from_rgb(30, 74, 213))
        em.add_field(name="Streak Summary", value=message)

        await interaction.response.send_message("Coming right up!")
        await interaction.channel.send(embed=em)
    except Exception as e:
        await interaction.response.send_message("You don't seem to have a goal recorded in our database. Please use '/startsoberjourney' to begin your streak!")
        print(str(e))

@client.tree.command(name = "resetsoberjourney", description = "If you've relapsed, broke your streak or want to start your timer over on your sober streak.")
#Reset time clean to 0
async def resetSoberJourney(interaction):
    collection.update_one({"_id" : interaction.user.id}, {
        "$set" : {"_since" : datetime.datetime.now()}
    })
    await interaction.response.send_message("Progress Reset. Remember, it doesn't matter how slowly you go as long as you don't stop!")

@client.tree.command(name = "changesoberjourney", description = "Have a new goal? Change your path!")
async def changeSoberJourney(interaction, journey : str):
    collection.update_one({"_id" : interaction.user.id}, {
        "$set" : {"_journey" : journey, "_since" : datetime.datetime.now()}
    })
    await interaction.response.send_message("Goal amended successfully. Good luck!")

@client.tree.command(name = "deletesoberjourney", description = "Erase your sober journey from the database")
async def deleteSoberJourney(interaction):
    collection.delete_one({"_id" : interaction.user.id})
    await interaction.response.send_message("Goal deleted successfully.")

@client.event
async def on_ready():
    print('connected to discord!')
    channel = client.get_channel(1045823574084169738)
    await client.tree.sync()
    await channel.send("i am a bot and do not care for your emotions, erika is a hot mommy, test successful")
    await asyncio.gather(
        regular_riddle.start(),
        quote_of_the_day.start()
        #Testoid
    )

@client.event
async def on_message(message):
    # //if "erika" in message.content:
    #     await message.channel.send("is a hot mommy")

    if message.type == discord.MessageType.premium_guild_subscription:
        await message.channel.send("New boost!!")
    if message.author.id == 906212102757294080 and filimemeo is True:
        await message.add_reaction('🇵🇭')
        await client.process_commands(message)
    if substring in message.content:
        resp = generate_response(message.content)
        if substring in resp:
            await message.channel.send("You thought you were slick with that recursive loop, didn't you")
        else:
            await message.channel.send(str(resp))
    else:
        await client.process_commands(message)



@tasks.loop(hours=24)
async def quote_of_the_day():
    quoteChannel = client.get_channel(1041717466633605130)
    response = requests.get("https://zenquotes.io/api/quotes/").json()
    await quoteChannel.send(response[0]['q'])
    await client.get_user(623602247921565747).send(response[0]['q'])


@tasks.loop(hours = 3)
async def regular_riddle():
    global answer
    riddleChannel = client.get_channel(1041718370564849775)
    response = requests.get("https://riddles-api.vercel.app/random").json()
    await client.get_user(623602247921565747).send(response['answer'])
    answer = response['answer']
    await riddleChannel.send(response['riddle'])


@client.command()
async def getQuote(ctx):
    response = requests.get("https://zenquotes.io/api/quotes/").json()
    print(response[0]['q'])

@client.command()
async def getRiddle(ctx):
    response = requests.get("https://riddles-api.vercel.app/random").json()
    await client.get_user(623602247921565747).send(response['answer'])
    print(response['riddle'])

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
    await ctx.channel.send("If you do not see an applicable phoneline in the provided list, consult findahelpline.com, findhelp.org for services specific to your area")


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
    riddleChannel = client.get_channel(1041718370564849775)
    ##await riddleChannel.send("I am fed up of waiting for you dumbasses, the riddle answer is + '" + answer + "'")
    print("Finished waiting")

@quote_of_the_day.before_loop
async def beforequote():
    await client.wait_until_ready()
    print("Quote ready")

client.run(TOKEN)