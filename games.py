import discord
import asyncio
from asyncio import gather
import pymongo
from discord.components import Button
import openai
import re
from collections import defaultdict
async def transfer(origin, to, amt, balances):

    ## First check both users exist, then check if sender has enough money.


    userbalance = balances.find_one({"_id": to})

    balance = userbalance["balance"]

    if userbalance is None:
        balances.insert_one({"_id": to, "balance": balance + 2000, "inventory": []})
    else:
        balance = userbalance["balance"]
        balances.update_one({"_id": to}, {"$set": {"balance": balance + 2000}})

    pass

async def depositMoney(to, amt, balances):
    userbalance = balances.find_one({"_id": to})

    balance = userbalance["balance"]

    if userbalance is None:
        balances.insert_one({"_id": to, "balance": balance + 2000, "inventory": []})
    else:
        balance = userbalance["balance"]
        balances.update_one({"_id": to}, {"$set": {"balance": balance + 2000}})

def findGameByID(ID, activelist):
    return activelist.get(ID, None)
class Game:
    def __init__(self, interaction, client):
        self.players = [interaction.user.id]
        self.active = False
        self.host = interaction.user.id
        self.interaction = interaction
        self.client = client
        self.gameID = None
        self.guild = interaction.guild
        self.misc = None
        self.gamePlatform = None


    async def setup(self, game, misc = None):
        embed = discord.Embed(
            title=f"{game} Lobby Created!",
            description=f"React with 🎮 to join the lobby! (1/5) | Host react with ▶️ to start!", ## Maybe try to include a max
            color=discord.Color.green()
        )

        if misc:
            embed.add_field(name="Details", value=misc)
            self.misc = misc

        embed.add_field(name="Players", value=self.player_list(self.guild), inline=False)


        await self.interaction.response.send_message("Starting the lobby now!", ephemeral=True)
        message = await self.interaction.channel.send(embed=embed)

        self.gameID = message.id
        print(self.gameID)
        # Add the game controller reaction
        await message.add_reaction("🎮")
        await message.add_reaction("▶️")

        return message

    async def addPlayer(self, player, lobby):
        self.players.append(player)
        embed = lobby.embeds[0]

        # Find the "Players" field and modify it
        for field in embed.fields:
            if field.name == "Players":
                field.value = self.player_list(lobby.guild)  # Passing the guild object
                break
        else:
            # If there isn't a "Players" field, add it
            embed.add_field(name="Players", value=self.player_list(lobby.guild), inline=False)

        embed.description = f"React with 🎮 to join the lobby! ({len(self.players)}/5)"

        await lobby.edit(embed=embed)

    def player_list(self, guild):
        return ", ".join(
            [guild.get_member(player_id).name for player_id in self.players if guild.get_member(player_id)])


async def generate_response(prompt):
    response_format = ("Generate 7 hard multiple choice questions on the topic of {0} with one correct answer and three wrong answers. "
                       "Each question should be followed by its four options labeled a) to d). After the options, provide the correct answer beginning with 'Correct answer:' "
                       "and then give the reasoning starting with 'Reasoning:'.").format(prompt)

    answer = openai.ChatCompletion.create(
        model='gpt-3.5-turbo',
        messages=[
            {"role": "user", "content": response_format}
        ],
        max_tokens=900,
        temperature=0,
    )

    message = answer['choices'][0]['message']['content']
    print(message)

    # Updated regular expression to extract the required parts
    pattern = (r'(?P<qnum>\d+\))\s(?P<question>.+?)\n?a\)\s(?P<option_a>.+?)\n?b\)\s(?P<option_b>.+?)'
               r'\n?c\)\s(?P<option_c>.+?)\n?d\)\s(?P<option_d>.+?)\n?Correct answer:\s(?P<answer>.+?)'
               r'\n?Reasoning:\s(?P<reasoning>.+?)(?=\n\d+\)|$)')

    matches = re.finditer(pattern, message, re.DOTALL)

    # Extract and structure the data
    results = []
    for match in matches:
        q_and_a = {
            "question": match.group("question").strip(),
            "options": [
                match.group("option_a").strip(),
                match.group("option_b").strip(),
                match.group("option_c").strip(),
                match.group("option_d").strip()
            ],
            "correct_answer": match.group("answer").strip(),
            "reasoning": match.group("reasoning").strip()
        }
        results.append(q_and_a)

    print(results)
    return results


class Quiz(Game):


    async def fetchQuestions(self):
        ## I want to conduct an API call while the game is loading in the background so the questions are preloaded
        resp = await generate_response(self.misc)
        return resp
        # await self.interaction.channel.send(resp)

    async def start_game_countdown(self, channel):
        start_embed = discord.Embed(title="Game Starting Soon!", description="Prepare for the questions!",
                                    color=discord.Color.blue())
        message = await channel.send(embed=start_embed)

        countdown_task = asyncio.create_task(self.run_countdown(message, start_embed, channel))
        fetch_task = asyncio.create_task(self.fetchQuestions())

        await asyncio.gather(countdown_task, fetch_task)
        return message, fetch_task.result()

    async def run_countdown(self, message, embed, channel):
        # Countdown loop
        for i in range(10, 0, -1):
            embed.description = f"Game starting in {i} seconds...\n\nPlayers:\n{self.player_list(channel.guild)}"
            await message.edit(embed=embed)
            await asyncio.sleep(1)


    async def startQuiz(self, lobbyChannel, gameArea, questions):
        player_answers = {}
        self.gamePlatform = gameArea.id
        answer_emojis = ["🇦", "🇧", "🇨", "🇩"]
        correct_counts = defaultdict(int)

        async def prune_reactions(gameArea):
            message = await gameArea.channel.fetch_message(gameArea.id)
            user_reactions = {}

            for reaction in message.reactions:
                if reaction.emoji in answer_emojis:
                    async for user in reaction.users():
                        if user.id == self.client.user.id:
                            continue
                        if user.id in user_reactions:
                            user_reactions[user.id].append(reaction.emoji)
                        else:
                            user_reactions[user.id] = [reaction.emoji]

            for user_id, emojis in user_reactions.items():
                if len(emojis) > 1:
                    for emoji in emojis[:-1]:
                        await message.remove_reaction(emoji, self.client.get_user(user_id))

        async def timer_and_pruner():
            for i in range(10, 0, -1):
                embed.set_footer(text=f"Time left: {i}s")
                await gameArea.edit(embed=embed)
                if i % 3 == 0:
                    asyncio.create_task(prune_reactions(gameArea))
                await asyncio.sleep(1)

        for index, question in enumerate(questions):
            embed = discord.Embed(
                title=f"Question {index + 1}",
                description=question["question"],
                color=discord.Color.blue()
            )

            for idx, option in enumerate(question["options"]):
                embed.add_field(name=answer_emojis[idx], value=option, inline=True)

            await gameArea.edit(embed=embed)

            for emoji in answer_emojis:
                await gameArea.add_reaction(emoji)

            await timer_and_pruner()

            await prune_reactions(gameArea)  # Final prune after timer ends

            embed.set_footer(text="Time's up!")
            await gameArea.edit(embed=embed)

            gameArea = await lobbyChannel.fetch_message(gameArea.id)
            correct_players = []
            correct_answer_content = question["correct_answer"].split(') ')[1]
            correct_answer_index = question["options"].index(correct_answer_content)

            for reaction in gameArea.reactions:
                if reaction.emoji in answer_emojis:
                    async for user in reaction.users():
                        if user.id != self.client.user.id:
                            player_answers[user.id] = reaction.emoji

                            if reaction.emoji == answer_emojis[correct_answer_index]:
                                correct_players.append(user.name)
                                correct_counts[user.id] += 1  # Increment the correct answer count for the player


            answer_embed = discord.Embed(
                title=f"The Correct Answer for Question {index + 1}",
                description=f"Correct Answer: {question['correct_answer']}\n\nReasoning: {question['reasoning']}",
                color=discord.Color.green()
            )

            for i in range(5, 0, -1):
                answer_embed.set_footer(
                    text=f"Next question in {i} seconds. Correct this round: {', '.join(correct_players) if correct_players else 'None'}")
                await gameArea.edit(embed=answer_embed)
                await asyncio.sleep(1)

            await gameArea.clear_reactions()

        sorted_counts = sorted(correct_counts.items(), key=lambda x: x[1], reverse=True)
        top_three = sorted_counts[:3]

        # Get their names
        top_three_names = [(self.client.get_user(user_id).name, count) for user_id, count in top_three]

        # Create a description string for the top 3
        top_three_str = "\n".join(
            [f"{i + 1}. {name} - {count} correct" for i, (name, count) in enumerate(top_three_names)])

        winner_embed = discord.Embed(
            title="Quiz Over!",
            description=f"Top 3:\n{top_three_str if top_three_names else 'No winners'}",
            color=discord.Color.gold()
        )

        await gameArea.edit(embed=winner_embed)

        return player_answers

    async def evaluateResults(self):
        pass



