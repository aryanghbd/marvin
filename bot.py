import asyncio
import random

import discord
from discord.ext import commands, tasks
from discord import Intents
from discord import app_commands
from discord.utils import get
import typing
import requests
import pymongo
from pymongo import MongoClient
import time
from datetime import datetime, timedelta
import openai
from pymongo import errors
import nacl
from discord import Interaction
from requests.auth import HTTPBasicAuth
from dateutil.parser import parse
import openai
import os
from dotenv import load_dotenv
import yt_dlp
from musicplayer import MusicPlayer

load_dotenv()

TOKEN = os.getenv('BOT_TOKEN')
MONGO_URL = os.getenv('MONGO_URL')
openai.api_key = os.getenv('OPENAI_KEY')

client = commands.Bot(command_prefix='$', intents = Intents.all())
cluster = MongoClient(MONGO_URL)
db = cluster["UserData"]
collection = db["SoberJournies"]
moodCollection = db["Moods"]
goalCollection = db["Goals"]

in_prog = False
answer = ""

ydl_opts = {
            'format': 'bestaudio',
            'default_search': 'ytsearch',  # Set default search to YouTube
            'noplaylist': True  # Only download single song, not playlist
        }

mp = MusicPlayer(ydl_opts)

def generate_response(prompt):
    answer = openai.ChatCompletion.create(
        model='gpt-3.5-turbo',
        messages=[
            {"role": "user", "content": f'Imagine you are a cute, friendly mental health support bot called Marvin (who is a small cuddly skeleton), which is where this API call comes from, someone is asking you the following, answer it in the spirit I described at the start: {prompt}'}],
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




'''
    Goals:
        -User puts in {GOAL}, {DUEBY} for their goal and due date/time
        
        -Bot will DM them periodically, to remind them.
        
        -Users can then 

'''


# A Context Menu command is an app command that can be run on a member or on a message by
# accessing a menu within the client, usually via right clicking.
# It always takes an interaction as its first parameter and a Member or Message as its second parameter.

# This context menu command only works on members


async def goal_autocompletion(
        interaction: discord.Interaction,
        current: str
) -> typing.List[app_commands.Choice[str]]:
    goalData = []
    choices = []

    user = goalCollection.find_one({"_id": interaction.user.id})

    goals = user.get('goals', [])
    for i, m in enumerate(goals):
        goalData.append(app_commands.Choice(name=str(m['goal']), value=m['goal']))

    return goalData



'''
    completegoal():
        -Privacy to toggle displaying completion publicly or not.
        
'''

@client.tree.command(name="deletegoal", description="Changed your mind on a goal? You can delete it with this.")
@app_commands.choices(privacy = [
    app_commands.Choice(name = 'Public', value = 1),
    app_commands.Choice(name = 'Private', value = 2),
])
@app_commands.autocomplete(item=goal_autocompletion)
async def deletegoal(interaction: discord.Interaction, item: str, privacy: app_commands.Choice[int]):
    user = goalCollection.find_one({"_id": interaction.user.id})

    goals = user.get('goals', [])
    for i, m in enumerate(goals):
        if m['goal'] == item:
            # Found a mood document for today, remove it
            goalCollection.update_one({"_id": interaction.user.id}, {"$pull": {"goals": {"goal": item}}})
            break

    if privacy.value == 1:
        await interaction.response.send_message(f"Goal deleted. No worries, there's always another day!")
    else:
        await interaction.response.send_message(f"Goal deleted. No worries, there's always another day!", ephemeral=True)

@client.tree.command(name="completegoal", description="Finished up on a goal? Go ahead and tick it off the list!")
@app_commands.choices(privacy = [
    app_commands.Choice(name = 'Public', value = 1),
    app_commands.Choice(name = 'Private', value = 2),
])
@app_commands.autocomplete(item=goal_autocompletion)
async def completegoal(interaction: discord.Interaction, item: str, privacy: app_commands.Choice[int]):

    user = goalCollection.find_one({"_id": interaction.user.id})

    goals = user.get('goals', [])
    for i, m in enumerate(goals):
        if m['goal'] == item:
            # Found a mood document for today, remove it
            goalCollection.update_one({"_id": interaction.user.id}, {"$pull": {"goals": {"goal": item}}})
            break

    if privacy.value == 1:
        await interaction.response.send_message(f"Great job on finishing off your goal of {item} <a:pucksalute:1116178939002494976>. Everyone, go give <@{interaction.user.id}> a high five!")
    else:
        await interaction.response.send_message(f"Hey there, good job on finishing off on {item}, enjoy those endorphins from having accomplished something today!", ephemeral=True)

@client.tree.command(name="setnewgoal", description="Feeling ambitious? Set a goal for a certain time!" )
@app_commands.choices(privacy = [
    app_commands.Choice(name = 'Public', value = 1),
    app_commands.Choice(name = 'Private', value = 2),
])
@app_commands.choices(accountability = [
    app_commands.Choice(name = 'DM me periodic reminders', value = 1),
    app_commands.Choice(name = 'Don`t DM me periodic reminders', value = 2),
])
async def setgoal(interaction: discord.Interaction, goal : str, days : int, hours : int, minutes : int, privacy : app_commands.Choice[int], accountability : app_commands.Choice[int]):
    date = datetime.now()

    by = date + timedelta(days=days, hours=hours, minutes=minutes)
    timedGoal = {"goal" : goal, "by" : by, "accountable" : accountability.value}

    user = goalCollection.find_one({"_id": interaction.user.id})

    if user is None:
        # User not found, create a new document
        goalCollection.insert_one({"_id": interaction.user.id, "goals": [timedGoal]})
        await interaction.response.send_message(f"Just set your goal, <@{interaction.user.id}>, wishing you good luck on: {goal}", ephemeral=privacy.value == 2)
    else:
        # User found
        if len(user.get('goals', [])) >= 7:
            await interaction.response.send_message(f"Sorry <@{interaction.user.id}>, looks like you've already got 7 active goals. I'm not a circus animal to be juggling all of those goals! Please complete or remove a goal before adding a new one.", ephemeral=True)
        else:
            # User has less than 7 goals, add a new goal to the existing goals array
            goalCollection.update_one({"_id": interaction.user.id}, {"$push": {"goals": timedGoal}})
            await interaction.response.send_message(f"Just set your goal, <@{interaction.user.id}>, wishing you good luck on: {goal}", ephemeral=privacy.value == 2)


# @client.tree.context_menu(name='Show Join Date')
# async def show_join_date(interaction: discord.Interaction, member: discord.Member):
#     # The format_dt function formats the date time into a human readable representation in the official client
#     await interaction.response.send_message(f'{member} joined at {discord.utils.format_dt(member.joined_at)}')

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

    await interaction.response.send_message("Thank you for sharing how you felt today, if no one else has told you today, remember that you are loved <a:booheartgreen:1052184874552938536>", ephemeral=True)


# @client.tree.command(name="marvinmoodtunes", description="How are you feeling? Tell Marvin, and he'll spin you some songs to help you through it")
# async def moodtunes(interaction, mood : str):
#     trusted = [229206808659492864, 922920299266179133, 706936739520053348, 1061788721973841930]
#     discord.opus.load_opus("/usr/local/Cellar/opus/1.4/lib/libopus.0.dylib")
#     if interaction.user.id not in trusted:
#         await interaction.response.send_message("Sorry loser, this command is under construction")
#     else:
#         await interaction.response.send_message("Let's think of something to suit the mood..")
#         prompt = (
#             "I'm looking for a list of 10 songs to match a certain mood or to reflect someone's day. "
#             "The mood/vent is: '{}'. "
#             "Please provide the song titles only, without any additional text or explanation. "
#             "For example: \n"
#             "1. Song Title 1\n"
#             "2. Song Title 2\n"
#             "3. Song Title 3\n"
#             "...\n"
#             "10. Song Title 10"
#         ).format(mood)
#         ans = await FetchGPTResponse(prompt)
#         q = ans.split('\n')
#         await interaction.channel.send(ans)
#
#         vc = client.get_channel(1041794802557132921)
#
#         conn = await vc.connect()
#
#         await mp.setInteraction(interaction)
#         await mp.setConnection(conn)
#
#         if conn:
#             # Add the first song to the queue
#             if q:
#                 await mp.add_to_queue(q.pop(0))
#
#             # Add next few songs to the queue before starting the player
#             for _ in range(min(2, len(q))):  # Add 2 songs, or whatever remains if less than 2
#                 await mp.add_to_queue(q.pop(0))
#
#             # Start the player
#             await mp.start()
#
#             # Schedule the task to add the remaining songs
#             async def add_remaining_songs():
#                 for song in q:
#                     await mp.add_to_queue(song)
#
#             asyncio.create_task(add_remaining_songs())
#
#
# @client.tree.command(name="queue", description="Check the current vent music queue")
# async def dumpQueue(interaction):
#     embed = discord.Embed(title="Song Queue")
#
#     # 'queue' is your deque object containing the songs
#     description = ""
#     for i, song in enumerate(mp.queue, start=1):
#         url, title = song
#         description += f"{i}. {title}\n"
#
#     embed.description = description
#     await interaction.response.send_message(embed=embed)
#
# @client.tree.command(name="pausesong", description="test")
# async def pausesong(interaction):
#     await interaction.response.send_message("Pausing!")
#     await mp.pause()
#
# @client.tree.command(name="resumesong", description="test")
# async def unpausesong(interaction):
#     await interaction.response.send_message("Resuming the tunes")
#     await mp.unpause()
# @client.tree.command(name="skipsong", description="Skip!")
# async def skip(interaction):
#     await interaction.response.send_message("Skipping this song!")
#     mp.skipSong()
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
        await interaction.response.send_message("I've been trying to find your mood data, but it looks like you haven't given me any. Go ahead and give it a try now with /checkup !", ephemeral=True)
    else:
        moods = user['moods']

        if not isinstance(moods, list):
            await interaction.response.send_message("Uh oh, there was an unexpected error trying to format your mood data. You're going to have to bring this up with my creator (<@:922920299266179133>)", ephemeral=True)
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
            em = discord.Embed(title= f"{interaction.user.name}'s Mood Chart ({time.name})", color=discord.Color.from_rgb(255, 105, 180).from_rgb(30, 74, 213))
            em.add_field(name="Details:", value=details)
            await interaction.response.send_message(embed = em, ephemeral= (privacy.name == 'Private'))


@client.tree.command(name = "report", description="Need to quietly report something to a mod? Use this command to send a ticket to the mod team.")
async def report(interaction, reason : str, details: str):
    em = discord.Embed(title=f"Report sent from: {interaction.user.name} | Details: {reason}", color=discord.Color.from_rgb(255, 105, 180).from_rgb(30, 74, 213))
    em.add_field(name="Further Information:", value=details)
    ticChannel = client.get_channel(1117079087928836127)
    await interaction.response.send_message("Thank you for submitting your report, let me pass this on to the mods, and they'll look into the matter for you.", ephemeral=True)
    await ticChannel.send(embed=em)
    ##therapy
@client.tree.command(name = "marvindraw", description="Marvin is a great artist, give him a prompt, and and turn your imagination into a picture!")
async def dalle(interaction, question: str):
    await interaction.response.send_message("Coming right up!")
    response = await makeImage(question)
    await interaction.channel.send(f"Alas, as requested: '{question}'")
    await interaction.channel.send(response)
@client.tree.command(name = "askmarvinanon", description="Whisper Marvin a question and get the response anonymously sent to your DM.")
async def askgptanonymous (interaction, question : str):
    await interaction.response.send_message("Coming right up! Let me think about it and then I'll DM you the answer.", ephemeral=True)
    response = await FetchGPTResponse(question)
    await interaction.user.send(f"Response to question: '{question}'")
    await interaction.user.send(str(response))

@client.tree.command(name= "anonymousvent", description="Want to get something off your chest, without your name showing up? Use this command.")
async def anonvent (interaction, topic : str, vent: str):
    ## Generate an embed
    em = discord.Embed(title=topic, color=discord.Color.from_rgb(255, 105, 180).from_rgb(30, 74, 213))
    em.add_field(name="Details:", value=vent)
    anonChannel = client.get_channel(1041718629345001513)
    loggings = client.get_channel(1047579544497954967)
    await interaction.response.send_message("Thank you for sharing that with me, hopefully you feel a bit better now you've got that off your chest. It takes a lot of strength to do that.", ephemeral=True)
    await anonChannel.send(embed=em)

    em.add_field(name="User: ", value = interaction.user.name)
    await loggings.send(embed=em)


@app_commands.choices(page = [
    app_commands.Choice(name = '1', value = 1),
    app_commands.Choice(name = '2', value = 2),
])

@client.tree.command(name="help", description="Wanna know what you can do with the Therapy Corner bot? Use this.")
async def help(interaction, page : app_commands.Choice[int]):
    em = discord.Embed(title="Bot Manual", color=discord.Color.from_rgb(255, 105, 180).from_rgb(30, 74, 213))
    em.add_field(name='\u200b', value="Hello! I'm Marvin! I'm the bot that serves the Therapy Corner community. Feel free to familiarize yourself with some of my commands so that you can get the most out of your time here.", inline=False)
    em.set_thumbnail(url="https://i.imgur.com/fr0tqjv.png")

    cmds = []
    for command in client.tree.walk_commands():
        cmds.append(f"```/{command.name}```\n{command.description}\n")

    half_index = len(cmds) // 2
    cmds_first_half = cmds[:half_index]
    cmds_second_half = cmds[half_index:]

    if page.value == 1:

        em.add_field(name='Marvin Commands (Page 1):', value='\n'.join(cmds_first_half))
    else:
        em.add_field(name='Marvin Commands (Page 2):', value='\n'.join(cmds_second_half))

    await interaction.response.send_message(embed=em, ephemeral=True)
@client.tree.command(name = "askmarvin", description="Ask Marvin a question and get an indepth response, publicly sent.")
async def askgpt (interaction, question : str):
    await interaction.response.send_message("Let me have a think about that first...")
    response = await FetchGPTResponse(question)
    await interaction.channel.send(f"Aha! I've got it, you wanted to ask: '{question}'")
    await interaction.channel.send(str(response))



@client.tree.command(name = "revealriddleanswer", description = "Reveal the answer to the Riddle") #Add the guild ids in which the slash command will appear. If it should be in all, remove the argument, but note that it will take some time (up to an hour) to register the command if it's for all guilds.
async def riddleanswer(interaction):
    await interaction.response.send_message("That one was a tough one! I'll give you the answer this time, its: " + answer + ". Better luck on the next riddle!")

@client.tree.command(name = "startsoberjourney", description = "Every journey begins with a single step")
async def startSoberJourney(interaction, journey : str):
    try:
        collection.insert_one({"_id" : interaction.user.id, "_journey" : journey, "_since" : datetime.now()})
        await interaction.response.send_message("I've recorded your journey in my system. I'm proud of you for starting, that's always the hardest step.")
    except pymongo.errors.DuplicateKeyError:
        await interaction.response.send_message(
            "Uh oh, it seems you already gave me a journey, I can't juggle two at the same time! Please delete your existing one, and then let me know what your new one is.")


@client.tree.command(name = "viewsoberjourney", description = "Reflect on your progress so far")
async def viewSoberJourney(interaction):
    try:
        entry = collection.find_one({"_id" : interaction.user.id})
        journey = entry.get("_journey")
        journeyStart = entry.get("_since")

        diff = (datetime.now() - journeyStart)
        total_days = diff.days
        weeks, days = divmod(total_days, 7)
        hours, remainder = divmod(diff.seconds, 3600)
        minutes, _ = divmod(remainder, 60)

        username = str(client.get_user(interaction.user.id))
        message = ("<@" + str(interaction.user.id) + ">") + ", time to look back on your progress! You've been working hard, staying clean from " + journey + " for %d weeks, %d days, %d hours and %d minutes now! Great job!" % (weeks, days, hours, minutes)

        em = discord.Embed(title= username + "'s Sober Journey", color=discord.Color.from_rgb(255, 105, 180).from_rgb(30, 74, 213))
        em.add_field(name="Streak Summary", value=message)

        await interaction.response.send_message("Coming right up!")
        await interaction.channel.send(embed=em)

    except Exception as e:
        await interaction.response.send_message("I'm sorry, it looks like you didn't give me a journey to track! Go ahead and use '/startsoberjourney' to begin your streak, I've got a sharp memory, I promise!")
        print(str(e))

@client.tree.command(name = "resetsoberjourney", description = "If you've relapsed, broke your streak or want to start your timer over on your sober streak.")
#Reset time clean to 0
async def resetSoberJourney(interaction):
    collection.update_one({"_id" : interaction.user.id}, {
        "$set" : {"_since" : datetime.now()}
    })
    await interaction.response.send_message("Sorry to hear that you relapsed, I hope everything's alright. I've reset your streak. Remember, it doesn't matter how slowly you go as long as you don't stop!")

@client.tree.command(name = "changesoberjourney", description = "Have a new goal? Change your path!")
async def changeSoberJourney(interaction, journey : str):
    collection.update_one({"_id" : interaction.user.id}, {
        "$set" : {"_journey" : journey, "_since" : datetime.now()}
    })
    await interaction.response.send_message("Goal amended successfully. Good luck!")

@client.tree.command(name = "deletesoberjourney", description = "Erase your sober journey from the database")
async def deleteSoberJourney(interaction):
    collection.delete_one({"_id" : interaction.user.id})
    await interaction.response.send_message("I cleared your journey from my database. Whatever your next journey is, I'll be there! <a:puckspin:1116178950956253264>")
    ##
@client.tree.command(name = "postembed", description = "Staff feature to post embeds")
async def postEmbed(interaction, colour : str, name : str, details : str):
    trusted = [229206808659492864, 922920299266179133, 706936739520053348, 1061788721973841930, 724261185310163045, 705099363499769897]
    if interaction.user.id not in trusted:
        interaction.response.send_message("Sorry, this command is for staff members only, git gud.")
    try:
        r, g, b = map(int, colour.split(','))
        emb = discord.Embed(title=name, color=discord.Color.from_rgb(r, g, b))
        emb.add_field(name="", value=details)
        await interaction.response.send_message("Serving up your embed right now!", ephemeral = True)
        await interaction.channel.send(embed=emb)
    except ValueError:
        await interaction.response.send_message("Marvin had a little whoopsie moment. I couldn't quite recognise your RGB input")


@client.event
async def on_ready():
    print('connected to discord!')
    channel = client.get_channel(1045823574084169738)
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=" you with /help"))
    await asyncio.gather(
        goalreminder.start(),
        regular_riddle.start(),
        quote_of_the_day.start(),
        checkupreminder.start()
    )
    await client.tree.sync()


@client.event
async def on_raw_reaction_remove(payload):
    channel = client.get_channel(1121336331675631687)
    if payload.message_id == 1121504128435232789 and payload.user_id != 1121456578529349814:
        guild = client.get_guild(payload.guild_id)
        user = guild.get_member(payload.user_id)
        msg = await channel.fetch_message(payload.message_id)
        yellowrole = discord.utils.find(lambda r: r.name == 'Yellow', guild.roles)
        limerole = discord.utils.find(lambda r: r.name == 'Lime', guild.roles)
        cyanrole = discord.utils.find(lambda r: r.name == 'Cyan', guild.roles)
        purplerole = discord.utils.find(lambda r: r.name == 'Purple', guild.roles)
        deeppinkrole = discord.utils.find(lambda r: r.name == 'Deep Pink', guild.roles)
        blackrole = discord.utils.find(lambda r: r.name == 'Black', guild.roles)

        colourRoles = [yellowrole, limerole, cyanrole, purplerole, deeppinkrole, blackrole]

        for role in colourRoles:
            if role in user.roles:
                await user.remove_roles(role)
                break
@client.event
async def on_raw_reaction_add(payload):

    print(payload.message_id)
    channel = client.get_channel(1121336331675631687)
    if payload.message_id == 1121504128435232789 and payload.member.id != 1121456578529349814:
        msg = await channel.fetch_message(payload.message_id)
        yellowrole = discord.utils.find(lambda r: r.name == 'Yellow', payload.member.guild.roles)
        limerole = discord.utils.find(lambda r: r.name == 'Lime', payload.member.guild.roles)
        cyanrole = discord.utils.find(lambda r: r.name == 'Cyan', payload.member.guild.roles)
        purplerole = discord.utils.find(lambda r: r.name == 'Purple', payload.member.guild.roles)
        deeppinkrole = discord.utils.find(lambda r: r.name == 'Deep Pink', payload.member.guild.roles)
        blackrole = discord.utils.find(lambda r: r.name == 'Black', payload.member.guild.roles)

        colourRoles = [yellowrole, limerole, cyanrole, purplerole, deeppinkrole, blackrole]

        for role in colourRoles:
            if role in payload.member.roles:
                await payload.member.send(f"Hey there, <@{payload.member.id}>! As much as I appreciate your desire to become the human embodiment of a rainbow, I'm afraid you can only hold on to one coloured role at a time! Please remove your current role before adding a new one.")
                await msg.remove_reaction(payload.emoji, payload.member)
                return

        if str(payload.emoji) == "🍋":
            role = get(payload.member.guild.roles, id = 1121371179769413673)
            await payload.member.add_roles(role)
        elif str(payload.emoji) == "🥝":
            role = get(payload.member.guild.roles, id = 1121370786754728028)
            await payload.member.add_roles(role)
        elif str(payload.emoji) == "🧊":
            role = get(payload.member.guild.roles, id = 1121370664360738847)
            await payload.member.add_roles(role)
        elif str(payload.emoji) == "🍇":
            role = get(payload.member.guild.roles, id = 1121370998575476777)
            await payload.member.add_roles(role)
        elif str(payload.emoji) == "🍒":
            role = get(payload.member.guild.roles, id = 1121372437234331708)
            await payload.member.add_roles(role)
        elif str(payload.emoji) == "🎱":
            role = get(payload.member.guild.roles, id = 1121372246657749073)
            await payload.member.add_roles(role)


@client.event
async def on_message(message):
    # //if "erika" in message.content:
    #     await message.channel.send("is a hot mommy")

    # if message.type == discord.MessageType.premium_guild_subscription:
        # await message.channel.send("New boost!!")
        ## Boost image?

    '''
        Booster Perk:
            -Custom channel
            -Access to ChatGPT-4 (role)

    '''
    await client.process_commands(message)


@tasks.loop(seconds=1)
async def goalreminder():

    intervals = [
        7 * 24 * 60 * 60,  # 7 days
        3 * 24 * 60 * 60,  # 3 days
        1 * 24 * 60 * 60,  # 1 day
        12 * 60 * 60,  # 12 hours
        6 * 60 * 60,  # 6 hours
        3 * 60 * 60,  # 3 hours
        1 * 60 * 60,  # 1 hour
    ]

    def format_interval(seconds):
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        days, hours = divmod(hours, 24)

        result = ""

        if days > 0:
            result += f"{days} Day{'s' if days > 1 else ''} "
        if hours > 0:
            result += f"{hours} Hour{'s' if hours > 1 else ''} "
        if minutes > 0:
            result += f"{minutes} Minute{'s' if minutes > 1 else ''} "
        return result.strip()

    now = datetime.now()
    users = goalCollection.find()

    for user in users:
        for goalData in user.get('goals', []):
            due_by = goalData['by']

            for interval in intervals:
                interval_start = due_by - timedelta(seconds=interval)
                interval_end = due_by - timedelta(seconds=interval) + timedelta(seconds=1)

                if interval_start <= now <= interval_end:
                    sendTo = await client.fetch_user(user['_id'])
                    await sendTo.send(f"What's up, <@{sendTo.id}>, just letting you know your goal of {goalData['goal']} is due in {format_interval(interval)}, best of luck!")
            if due_by <= now < due_by + timedelta(seconds=1) and goalData['accountable'] == 1:
                sendTo = await client.fetch_user(user['_id'])
                await sendTo.send(f"Hey there <@{sendTo.id}>, just wanted to check up on you and see if you were finishing up on {goalData['goal']}? The due date is right about now according to my calculations <:frogleafy:1116179012310540370>, no pressure if you haven't though! It's important to go at your own pace, so let me know whenever you're done. If you've already finished your goal, feel free to /completegoal it, otherwise if you've changed your mind you can /deletegoal!")


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
    await quoteChannel.send(response[0]['q'] + ' | <@1125101346308247552>')
    await client.get_user(623602247921565747).send(response[0]['q'])


@tasks.loop(hours = 3)
async def regular_riddle():
    global answer
    riddleChannel = client.get_channel(1041718370564849775)
    response = requests.get("https://riddles-api.vercel.app/random").json()
    answer = response['answer']
    print(response['riddle'])
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