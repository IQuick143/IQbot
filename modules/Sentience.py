from discord.ext import commands
from util import check_if_owner

class SentientCog(commands.Cog, name='XKCD'):
	def __init__(self, bot):
		self.bot = bot

	@commands.command("set_channel", pass_context=True, description="Set destination by channel ID")
	@commands.check(check_if_owner)
	@commands.dm_only()
	async def set_channel(self, ctx, channel: int):
		self.channel = self.bot.get_channel(channel)
		if self.channel is None:
			await ctx.send("Can't find the channel")
			return
		await ctx.send("Found channel:" + self.channel.name)

	@commands.command("send", pass_context=True, description="Send a message to a given channel")
	@commands.check(check_if_owner)
	@commands.dm_only()
	async def send_msg(self, ctx, *, msg = ""):
		if msg == "":
			await ctx.send("You need to tell me what to send")
		else:
			if self.channel is None:
				await ctx.send("No destination set")
			await self.channel.send(msg)

def setup(bot):
	cog = SentientCog(bot)
	bot.add_cog(cog)

def teardown(bot): 
	pass
