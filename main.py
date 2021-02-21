import asyncio
import util

import discord
from discord import utils
from discord.ext import commands

import data.secrets as secrets
import data.settings as settings

# --- Settings ---

bot = commands.Bot(
	"!",
	case_insensitive=True
)

@bot.event
async def on_ready():
	print("*hacker voice* I'm in... I am " + str(bot.user))

@bot.event
async def on_message(message):
	await bot.process_commands(message)

"""
@bot.command(name="test_react")
async def test_react(ctx: commands.Context):
	msg = await ctx.send("Sure thing boss")
	async def on_roger(*args):
		await args[0].edit(content=args[1])
		return (True, args[1] + " roger")
	async def no_roger(*args):
		await args[0].delete()
		return False
	await util.react_interactive_message(bot, msg, react={
		util.emojis.check_mark: on_roger,
		util.emojis.cross: no_roger
	}, state="Roger")
"""

@bot.command(name="restart", aliases=["rs"], category=util.cat.admin)
@commands.check(util.check_if_owner)
async def _restart_bot(ctx: commands.Context):
	"""Restarts the bot."""
	global exit_code
	await util.add_react(ctx.message, util.emojis.check_mark)
	print(f"[**] Restarting! Requested by {ctx.author}.")
	exit_code = 42  # Signals to the wrapper script that the bot needs to be restarted.
	await bot.logout()

@bot.command(name="shutdown", aliases=["shut"], category=util.cat.admin)
@commands.check(util.check_if_owner)
async def _shutdown_bot(ctx: commands.Context):
	"""Shuts down the bot."""
	global exit_code
	await util.add_react(ctx.message, util.emojis.check_mark)
	print(f"[**] Shutting down! Requested by {ctx.author}.")
	exit_code = 0  # Signals to the wrapper script that the bot should not be restarted.
	await bot.logout()


@bot.group(name="extctl", aliases=["ex"], case_insensitive=True, category=util.cat.admin)
@commands.check(util.check_if_owner)
async def _extctl(ctx: commands.Context):
	"""Extension control commands.
	Defaults to `list` if no subcommand specified"""
	if ctx.invoked_subcommand is None:
		cmd = _extctl_list
		await ctx.invoke(cmd)


@_extctl.command(name="list", aliases=["ls"])
async def _extctl_list(ctx: commands.Context):
	"""Lists loaded extensions."""
	embed = util.embed_factory(ctx)
	embed.title = "Loaded Extensions"
	embed.description = "\n".join(["‣ " + x.split(".")[1] for x in bot.extensions.keys()])
	await ctx.send(embed=embed)


@_extctl.command(name="load", aliases=["ld"])
async def _extctl_load(ctx: commands.Context, extension: str):
	"""Loads an extension."""
	bot.load_extension(settings.ext_dir + "." + extension)
	await util.add_react(ctx.message, util.emojis.check_mark)


@_extctl.command(name="reload", aliases=["rl"])
async def _extctl_reload(ctx: commands.Context, extension: str):
	"""Reloads an extension."""
	bot.reload_extension(settings.ext_dir + "." + extension)
	await util.add_react(ctx.message, util.emojis.check_mark)


@_extctl.command(name="unload", aliases=["ul"])
async def _extctl_unload(ctx: commands.Context, extension: str):
	"""Unloads an extension."""
	bot.unload_extension(settings.ext_dir + "." + extension)
	await util.add_react(ctx.message, util.emojis.check_mark)


bot.load_extension(settings.ext_dir + ".MC")
bot.load_extension(settings.ext_dir + ".xkcd")
bot.load_extension(settings.ext_dir + ".Sentience")

bot.run(secrets.TOKEN)

exit(exit_code)
