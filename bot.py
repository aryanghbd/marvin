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
from pymongo import errors
from requests.auth import HTTPBasicAuth

TOKEN = "MTA0NjA0ODM0NDE5MzExNDE3Mw.GOLvSP.gqnjFwo3wsUwgNaK_ptSO0fgNNt1Sz7NNH7Tbg"

url = "https://discord.com/api/v10/applications/1046048344193114173/commands"

client = commands.Bot(command_prefix='$', intents = Intents.all())
cluster = MongoClient("mongodb+srv://tcadmin:erikamommy123@cluster0.9wobd.mongodb.net/test")
db = cluster["UserData"]
collection = db["SoberJournies"]


filimemeo = False
in_prog = False
answer = ""
import openai

openai.api_key = "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"

substring = "-gpt"
def generate_response(prompt):
    answer = openai.ChatCompletion.create(
        model='gpt-3.5-turbo',
        messages=[
            {"role": "user", "content": f'{prompt}'}],
        max_tokens=193,
        temperature=0,
    )
    

    message = answer['choices'][0]['message']['content']
    print(message)
    return message.strip()


def generate_image(prompt):
    response = openai.Image.create(
        prompt=prompt,
        n = 1,
        size = "256x256",
    )

    return response["data"][0]["url"]

helper_questions = ["Are you comfortable with triggering topics?", "Are you willing to stay active in order to help people as a councillor?", "Are you aware of most mental disorders?", "Do you have experience with counselling people?", "Are you at least a little familiar to the psychology field?", "Are you able to handle stress/anxiety well?",
                    "Are you able to keep a positive mood at all times?", "Would you consider your feelings being more important than the person you are and will be helping?", "Do you know any methods to help people who have trauma?",
                    "Do you track mental health data and is it important to you?"]

async def FetchGPTResponse(question):
    resp = (generate_response(question))
    return resp

async def makeImage(question):
    resp = generate_image(question)
    return resp
@client.tree.command(name = "makeaiart", description="Wield the power of AI and turn your imagination into a picture! Type in a prompt and see.")
async def dalle(interaction, question: str):
    await interaction.response.send_message("Coming right up!")
    response = await makeImage(question)
    await interaction.channel.send(f"Alas, as requested: '{question}'")
    await interaction.channel.send(response)
@client.tree.command(name = "askgptanon", description="Ask a question and get an AI response anonymously sent to your DM.")
async def askgptanonymous (interaction, question : str):
    await interaction.response.send_message("Working on it. Please check your DMs for a response to your anonymous question.", ephemeral=True)
    response = await FetchGPTResponse(question)
    await interaction.user.send(f"Response to question: '{question}'")
    await interaction.user.send(str(response))

@client.tree.command(name= "anonymousvent", description="Want to get something off your chest, without your name showing up? Use this command.")
async def anonvent (interaction, topic : str, vent: str):
    ## Generate an embed
    em = discord.Embed(title=topic, color=discord.Color.from_rgb(30, 74, 213))
    em.add_field(name="Details:", value=vent)
    anonChannel = client.get_channel(1041718629345001513)
    await interaction.response.send_message("Thank you for submitting your vent, it takes a lot of strength to do that.", ephemeral=True)
    await anonChannel.send(embed=em)

@client.tree.command(name="help", description="Wanna know what you can do with the Therapy Corner bot? Use this.")
async def help(interaction):
    em = discord.Embed(title="Bot Manual", color=discord.Color.from_rgb(30, 74, 213))
    em.add_field(name='\u200b', value="Hello! I am the bot that serves the Therapy Corner community. Feel free to familiarize yourself with some of my commands so that you can get the most out of your time here.", inline=False)
    em.set_thumbnail(url="https://i.imgur.com/fr0tqjv.png")

    cmds = []
    for command in client.tree.walk_commands():
        cmds.append(f"```/{command.name}```\n{command.description}\n")

    em.add_field(name='Bot Commands:', value='\n'.join(cmds))

    await interaction.response.send_message(embed=em, ephemeral=True)
@client.tree.command(name = "askgpt", description="Ask a question and get an AI response, publicly sent.")
async def askgpt (interaction, question : str):
    await interaction.response.send_message("Working on it.")
    response = await FetchGPTResponse(question)
    await interaction.channel.send(f"Response to question: '{question}'")
    await interaction.channel.send(str(response))



@client.tree.command(name = "revealriddleanswer", description = "Reveal the answer to the Riddle") #Add the guild ids in which the slash command will appear. If it should be in all, remove the argument, but note that it will take some time (up to an hour) to register the command if it's for all guilds.
async def riddleanswer(interaction):
    await interaction.response.send_message("Damn you must suck at riddles, L bozo. The answer to the current riddle is: " + answer)

@client.tree.command(name = "startsoberjourney", description = "Every journey begins with a single step")
async def startSoberJourney(interaction, journey : str):
    try:
        collection.insert_one({"_id" : interaction.user.id, "_journey" : journey, "_since" : datetime.datetime.now()})
        await interaction.response.send_message("Journey recorded! Good luck!")
    except pymongo.errors.DuplicateKeyError:
        await interaction.response.send_message(
            "You appear to already have a goal recorded in our database. Please delete your existing one before starting a new one.")


@client.tree.command(name = "viewsoberjourney", description = "Reflect on your progress so far")
async def viewSoberJourney(interaction):
    try:
        entry = collection.find_one({"_id" : interaction.user.id})
        journey = entry.get("_journey")
        journeyStart = entry.get("_since")

        diff = (datetime.datetime.now() - journeyStart)
        total_days = diff.days
        weeks, days = divmod(total_days, 7)
        hours, remainder = divmod(diff.seconds, 3600)
        minutes, _ = divmod(remainder, 60)

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
    await channel.send("Test Mode toggled.")
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