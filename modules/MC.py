from data.settings import CANSTI_ID
import discord
from discord.ext import commands
from lib.rcon import RCON, RCONUnavailableException
import json
import aiohttp
from urllib.parse import quote

WHITELISTED = "data/whitelisted.txt"

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
				await ctx.send("The account is already used for another user "+str(already_whitelisted[ID]), allowed_mentions=discord.AllowedMentions.none())
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

def setup(bot):
	cog = MCCog(bot)
	cog.RCON = RCON()
	bot.add_cog(cog)

def teardown(bot):
	pass
