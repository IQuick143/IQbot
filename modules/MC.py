import re
from data.settings import CANSTI_ID
import discord
from discord.ext import commands
from lib.rcon import RCON, RCONUnavailableException
import json
import aiohttp
from urllib.parse import quote
from util import check_if_owner

WHITELISTED = "data/whitelisted.txt"
BLACKLISTED = "data/blacklisted.txt"

class MCCog(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	@commands.command("mcregister", pass_context=True, description="Get access to the Cansti SMP\nRequires user to be a member of Cansti.")
	async def mc_register(self, ctx, minecraft_username: str):
		if not ctx.author.bot:
			if ctx.guild is None or ctx.guild.id != CANSTI_ID:
				await ctx.send("This command is available only in the Canstitution Discord server.")
				return

			ID = str(ctx.author.id)
			with open(BLACKLISTED, "r") as fp:
				blacklisted = json.load(fp)
				if ID in blacklisted and blacklisted[ID]:
					await ctx.send("A higher power has intervened in me executing this command, please contact the local manager.")
					return
			UUID = ""
			async with aiohttp.ClientSession() as session:
				async with session.get("https://api.mojang.com/users/profiles/minecraft/"+quote(minecraft_username, safe="")) as resp:
					text = ""
					text = (await resp.text())
					if resp.status == 200:
						parsed = json.loads(text)
						minecraft_username = parsed["name"]
						UUID = parsed["id"]
					elif resp.status == 204:
						await ctx.send("The name "+str(minecraft_username)+" doesn't currently exist.", allowed_mentions=discord.AllowedMentions.none())
						return
					elif resp.status == 400:
						await ctx.send("The name "+str(minecraft_username)+" is invalid.", allowed_mentions=discord.AllowedMentions.none())
						return
					else:
						await ctx.send("There was likely an error connecting to the minecraft servers, please try again later.", allowed_mentions=discord.AllowedMentions.none())
						return

			with open(WHITELISTED, "r") as fp:
				already_whitelisted = json.load(fp)

			if UUID in already_whitelisted.values() and not (ID in already_whitelisted and already_whitelisted[ID] == UUID):
				ID_for_UUID = [k for k,v in already_whitelisted.items() if v == UUID]
				await ctx.send(f"The account is already used for <@!{ID_for_UUID[0]}>", allowed_mentions=discord.AllowedMentions.none())
				return

			try:
				if ID in already_whitelisted and already_whitelisted[ID] != UUID:
					async with aiohttp.ClientSession() as session:
						async with session.get(f"https://api.mojang.com/user/profiles/{quote(already_whitelisted[ID], safe='')}/names") as resp:
							text = ""

							text = (await resp.text())
							if resp.status == 200:
								parsed = json.loads(text)
								old_username = parsed[-1]["name"]
							else:
								await ctx.send("There was likely an error connecting to the minecraft servers, please try again later.", allowed_mentions=discord.AllowedMentions.none())
								return

					print(await self.RCON.send(f"whitelist remove {old_username}"))
				print(await self.RCON.send(f"whitelist add {minecraft_username}"))
				with open(WHITELISTED, "r") as fp:
					already_whitelisted = json.load(fp)
				already_whitelisted[ID] = UUID
				with open(WHITELISTED, "w") as fp:
					json.dump(already_whitelisted, fp)
				await ctx.send("You've been added to the Cansti SMP")
			except RCONUnavailableException:
				await ctx.send("The Cansti SMP server is currently unavailable, please try again later.")

	@commands.check(check_if_owner)
	@commands.command("mcban", pass_context=True, description="Ban access to the Cansti SMP\nRequires user to be IQbot admin.")
	async def mc_ban(self, ctx, discord_id: int):
		if not ctx.author.bot:
			await ctx.send("I sure hope that is a real ID of a real user...")
			
			discord_id = str(discord_id)

			with open(WHITELISTED, "r") as fp:
				whitelist = json.load(fp)
			if discord_id in whitelist:
				await ctx.send("Person is whitelisted, removing...")
				try:
					async with aiohttp.ClientSession() as session:
						async with session.get(f"https://api.mojang.com/user/profiles/{quote(whitelist[discord_id], safe='')}/names") as resp:
							text = ""
							text = (await resp.text())
							if resp.status == 200:
								parsed = json.loads(text)
								old_username = parsed[-1]["name"]
							else:
								await ctx.send("Failed to resolve UUID to account name. Please try again later.")
								return

						print(await self.RCON.send(f"whitelist remove {old_username}"))

						del whitelist[discord_id]

						with open(WHITELISTED, "w") as fp:
							json.dump(whitelist, fp)
					await ctx.send("Removed user from server whitelist")
				except RCONUnavailableException:
					await ctx.send("The Cansti SMP server is currently unavailable, please try again later.")
					return
			else:
				await ctx.send("Person wasn't even whitelisted lmao...")
			await ctx.send("Blacklisting person...")
			with open(BLACKLISTED, "r") as fp:
				blacklist = json.load(fp)
			blacklist[discord_id] = True
			with open(BLACKLISTED, "w") as fp:
				json.dump(blacklist, fp)
			
			await ctx.send("Congratulations, you have just banned someone from your minecraft server!")

	@commands.check(check_if_owner)
	@commands.command("mcunban", pass_context=True, description="Lift a ban on the access to the Cansti SMP\nRequires user to be IQbot admin.")
	async def mc_unban(self, ctx, discord_id: int):
		if not ctx.author.bot:
			await ctx.send("I sure hope that is a real ID of a real user...")
			
			discord_id = str(discord_id)

			with open(BLACKLISTED, "r") as fp:
				blacklist = json.load(fp)
			if discord_id in blacklist and blacklist[discord_id]:
				await ctx.send("YOUR WISH SHALL BE GRANTED.")
				blacklist[discord_id] = False
				with open(BLACKLISTED, "w") as fp:
					json.dump(blacklist, fp)
				return
			else:
				await ctx.send("Bruh that poor lad wasn't even banned.")
				return

def setup(bot):
	cog = MCCog(bot)
	cog.RCON = RCON()
	bot.add_cog(cog)

def teardown(bot):
	pass
