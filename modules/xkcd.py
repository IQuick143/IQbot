from discord.ext import commands, tasks
import json
import aiohttp
from fuzzywuzzy.fuzz import WRatio
import datetime
import util
from util import paths, check_if_owner, react_interactive_message

class XKCDCog(commands.Cog, name='XKCD'):
	def __init__(self, bot):
		self.bot = bot
		self.update_index.start()

	def cog_unload(self):
		self.update_index.cancel()

	@commands.command("xkcd_index", pass_context=True)
	@commands.check(check_if_owner)
	async def xkcd_index(self, ctx):
		await self.update_index()
		await util.add_react(ctx.message, util.emojis.check_mark)

	@commands.command("xkcd", pass_context=True, description="Get an xkcd comic. Default returns newest comic, otherwise allows person to search using a [querry]")
	async def xkcd(self, ctx, *, querry = ""):
		if querry:
			querry = querry.strip()
			try:
				num = int(querry)
				async with aiohttp.ClientSession() as session:
					async with session.get("https://xkcd.com/"+str(num)+"/info.0.json") as resp:
						if resp.status == 200:
							await ctx.send("https://xkcd.com/"+str(num)+"/")
						elif resp.status == 404:
							await ctx.send("There's currently no xkcd with that number.")
						else:
							await ctx.send("There was an error with xkcd servers try again later.")
				return
			except ValueError:
				pass
			results = await self.search(querry, 10)
			msg = await ctx.send(results[0]["link"])
			async def back(*args):
				num = args[1] - 1
				if num < 0: num = 0
				await args[0].edit(content=results[num]["link"])
				return (True, num)
			async def fow(*args):
				num = args[1] + 1
				if num > 9: num = 9
				await args[0].edit(content=results[num]["link"])
				return (True, num)
			async def close(*args):
				await args[0].delete()
				return False
			await react_interactive_message(self.bot, msg, {
				util.emojis.backward: back,
				util.emojis.foward: fow,
				util.emojis.cross: close
			}, caller=ctx.author, state=0)
		else:
			await ctx.send("https://xkcd.com/")

	async def search(self, querry, num_results=10):
		candiates = [{"key": k, "link": v["link"], "rating": WRatio(v["title"], querry)} for k, v in self.index.items()]
		
		return sorted(candiates, key=lambda v: -v["rating"])[:num_results]

	@tasks.loop(seconds=22000)
	async def update_index(self):
		changed = False
		async with aiohttp.ClientSession() as session:
			async with session.get("https://xkcd.com/info.0.json") as resp:
				text = ""
				text = (await resp.text())
				if resp.status == 200:
					parsed = json.loads(text)
					num = parsed["num"]
					if self.latest + 1 < num:
						self.missing_from_index.extend(list(range(self.latest + 1, num)))
					if self.latest < num:
						self.add_index(str(num), parsed)
						changed = True
					self.latest = num
				elif resp.status == 404:
					print("BIG ERROR: XKCD INFO.JSON NOT FOUND")

			for miss in self.missing_from_index:
				async with session.get("https://xkcd.com/"+str(miss)+"/info.0.json") as resp:
					text = ""
					text = (await resp.text())
					if resp.status == 200:
						parsed = json.loads(text)
						self.add_index(str(miss), parsed)
						changed = True
						self.missing_from_index.remove(miss)
					elif resp.status == 404:
						self.missing_from_index.remove(miss)
					else:
						print("Error at "+str(miss))
						pass

		if changed:
			self.save_index()

	def add_index(self, ID, info_json):
		print("Adding "+ID+" to the xkcd index")
		self.index[ID] = {
			"link": "https://xkcd.com/"+ID+"/",
			"title": info_json["title"],
			"transcript": info_json["transcript"],
			"alt": info_json["alt"]
		}

	def load_index(self, file = paths.data / "xkcd/index.json"):
		with open(file, "r") as fp:
			raw = json.load(fp)
		self.index = raw["data"]
		self.missing_from_index = raw["missing"]
		self.latest = raw["latest"]

	def save_index(self, file = paths.data / "xkcd/index.json"):
		with open(file, "w") as fp:
			json.dump({
				"last-changed": str(datetime.datetime.now()),
				"latest": self.latest,
				"missing": self.missing_from_index,
				"data": self.index
			}, fp)

def setup(bot):
	cog = XKCDCog(bot)
	cog.load_index()
	bot.add_cog(cog)

def teardown(bot): 
	pass
