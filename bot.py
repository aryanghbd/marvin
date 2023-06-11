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
from datetime import datetime, timedelta
import openai
from pymongo import errors
from discord import Interaction
from requests.auth import HTTPBasicAuth

TOKEN = "MTA0NjA0ODM0NDE5MzExNDE3Mw.GOLvSP.gqnjFwo3wsUwgNaK_ptSO0fgNNt1Sz7NNH7Tbg"

url = "https://discord.com/api/v10/applications/1046048344193114173/commands"

client = commands.Bot(command_prefix='$', intents = Intents.all())
cluster = MongoClient("mongodb+srv://tcadmin:erikamommy123@cluster0.9wobd.mongodb.net/test")
db = cluster["UserData"]
collection = db["SoberJournies"]
moodCollection = db["Moods"]


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


async def FetchGPTResponse(question):
    resp = (generate_response(question))
    return resp

async def makeImage(question):
    resp = generate_image(question)
    return resp


'''
    Checkups:
        - Role that can be selected to be reminded
        - At a certain point of the day (can be random or can be scheduled) - bot reminds users to check in
        - Users can then use /checkup - ephermal copmmand that brings up list of emoji reacts, react is then used and sent to MongoDB:
            -Keyed in under their user.ID, the subdocument will be the date
            
        - Users can then use /checkupchart - walk DB under their ID, tally up the emojis, organise into an embed.
        
        - Optional: Perhaps ChatGPT can give suggestions or affirmations.
'''




@client.tree.command(name = "checkupinfo", description="Wanna know how to track your mood during your time on Therapy Corner?")
async def checkuphelp(interaction):
    await interaction.response.send_message('''
    
    You can use the ```/checkup {MOOD}``` command once per day with the following selections:
    <:1_EmojiGreat:1117161493482455100> <:1_EmojiGood:1117161482786975905> <:1_EmojiMeh:1117161472418644119> <:1_EmojiBad:1117161462364897390> <:1_EmojiTerrible:1117161452495704095>
    Great | Good | Neutral | Bad | Terrible
    
    We also optionally @ you once daily at a random time to remind you if you like to stay accountable! 
    
    Over time, you can use the ```/checkupstats {MONTH, WEEK, ALL-TIME}``` to get your mood results in a chart format, out of the week, the month, or all-time.
    
    -Separate role to sign up 
    ''', ephemeral=True)

@client.tree.command(name = "checkup", description="How are you feeling today? Let's check up on you.")
@app_commands.choices(mood = [
    app_commands.Choice(name = 'Great', value = 1),
    app_commands.Choice(name = 'Good', value = 2),
    app_commands.Choice(name = 'Neutral', value = 3),
    app_commands.Choice(name = 'Bad', value = 4),
    app_commands.Choice(name = 'Terrible', value = 5)
])
async def checkup(interaction, mood : app_commands.Choice[int]):
    today = str(datetime.now().date())
    dailyMood = {"date": today, "mood": mood.name}

    user = moodCollection.find_one({"_id": interaction.user.id})

    if user is None:
        # User not found, create a new document
        moodCollection.insert_one({"_id": interaction.user.id, "moods": [dailyMood]})
    else:
        # User found, check if a mood document for today already exists
        moods = user.get('moods', [])
        for i, m in enumerate(moods):
            if m['date'] == today:
                # Found a mood document for today, remove it
                moodCollection.update_one({"_id": interaction.user.id}, {"$pull": {"moods": {"date": today}}})
                break
        # Whether the mood document for today existed or not, push the new one
        moodCollection.update_one({"_id": interaction.user.id}, {"$push": {"moods": dailyMood}})

    await interaction.response.send_message("Thank you for checking up.", ephemeral=True)



@client.tree.command(name= "checkupstats", description="Look back at how far you've come, generate a chart of your mood over time.")
@app_commands.choices(time = [
    app_commands.Choice(name = 'Last 7 Days', value = 1),
    app_commands.Choice(name = 'Last 30 Days', value = 2),
    app_commands.Choice(name = 'All-time', value = 3),
])

@app_commands.choices(privacy = [
    app_commands.Choice(name = 'Public', value = 1),
    app_commands.Choice(name = 'Private', value = 2),
])

async def checkupstats(interaction, privacy: app_commands.Choice[int], time : app_commands.Choice[int]):
    user = moodCollection.find_one({"_id" : interaction.user.id})

    emojis = {
        'Great' : '<:1_EmojiGreat:1117161493482455100>',
        'Good' : '<:1_EmojiGood:1117161482786975905>',
        'Neutral' : '<:1_EmojiMeh:1117161472418644119>',
        'Bad' : '<:1_EmojiBad:1117161462364897390>',
        'Terrible' : '<:1_EmojiTerrible:1117161452495704095>'
    }
    if user is None:
        await interaction.response.send_message("No mood data found for this user.", ephemeral=True)
    else:
        moods = user['moods']

        if not isinstance(moods, list):
            await interaction.response.send_message("Mood data is not in the expected format.", ephemeral=True)
        else:
            if time.name == 'Last 7 Days':
                moods = [m for m in moods if datetime.strptime(m['date'], "%Y-%m-%d").date() >= datetime.now().date() - timedelta(days=7)]
            elif time.name == 'Last 30 Days':
                moods = [m for m in moods if datetime.strptime(m['date'], "%Y-%m-%d").date() >= datetime.now().date() - timedelta(days=30)]
            # For 'All Time' no filtering is needed

            mood_counts = {'Great' : 0, 'Good' : 0, 'Neutral' : 0, 'Bad' : 0, 'Terrible' : 0}
            for mood in moods:
                mood_counts[mood['mood']] += 1

            details = "\n".join([f" {emojis[mood]} ({mood}): {count}" for mood, count in mood_counts.items()])
            em = discord.Embed(title= f"{interaction.user.name}'s Mood Chart ({time.name})", color=discord.Color.from_rgb(30, 74, 213))
            em.add_field(name="Details:", value=details)
            await interaction.response.send_message(embed = em, ephemeral= (privacy.name == 'Private'))


@client.tree.command(name = "report", description="Need to quietly report something to a mod? Use this command to send a ticket to the mod team.")
async def report(interaction, reason : str, details: str):
    em = discord.Embed(title=f"Report sent from: {interaction.user.name} | Details: {reason}", color=discord.Color.from_rgb(30, 74, 213))
    em.add_field(name="Further Information:", value=details)
    ticChannel = client.get_channel(1117079087928836127)
    await interaction.response.send_message("Thank you for submitting your report, a mod will look into the matter for you.", ephemeral=True)
    await ticChannel.send(embed=em)
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
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=" you with /help"))
    await asyncio.gather(
        regular_riddle.start(),
        quote_of_the_day.start(),
        checkupreminder.start()
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



@tasks.loop(hours = 24)
async def checkupreminder():
    channel = client.get_channel(1042415779393589268)
    minTime = 1000
    maxTime = 100000
    await asyncio.sleep(random.randint(minTime, maxTime))
    await channel.send('''<@&1117527753110065162>: Time for your daily check up! How are you feeling? Select from the following: 
    <:1_EmojiGreat:1117161493482455100> <:1_EmojiGood:1117161482786975905> <:1_EmojiMeh:1117161472418644119> <:1_EmojiBad:1117161462364897390> <:1_EmojiTerrible:1117161452495704095>
    Great | Good | Neutral | Bad | Terrible - Log it with ```/checkup {MOOD}```''')
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