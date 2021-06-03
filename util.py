import traceback
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Generator, Dict, Any, Tuple, Union, Coroutine

import aiohttp
import asyncio

import discord
from discord.errors import HTTPException
import discord.ext.commands as commands
from discord import Emoji, Reaction, PartialEmoji

import data.settings as settings

__all__ = ["colours", "cat", "emojis", "paths",
		   "embed_factory", "error_embed_factory", "add_react", "check_if_owner"]


# --- Common values ---

colours = SimpleNamespace(
	good=0x43B581,
	neutral=0x7289DA,
	bad=0xF04747,
)

# meow
cat = SimpleNamespace(
	lookup="Information Lookup",
	fun="Fun",
	maps="Mapping",
	ref="Reference",
	study="Exam Study",
	weather="Land and Space Weather",
	admin="Bot Control",
)

emojis = SimpleNamespace(
	check_mark="✅",
	cross="❌",
	warning="⚠️",
	question="❓",
	no_entry="⛔",
	bangbang="‼️",
	foward="▶",
	backward="◀",
	a="🇦",
	b="🇧",
	c="🇨",
	d="🇩",
)

paths = SimpleNamespace(
	data=Path("./data/")
)

# --- Exceptions ---

class BotHTTPError(Exception):
	"""Raised whan a requests fails (status != 200) in a command."""
	def __init__(self, response: aiohttp.ClientResponse):
		msg = f"Request failed: {response.status} {response.reason}"
		super().__init__(msg)
		self.response = response
		self.status = response.status
		self.reason = response.reason


# --- Helper functions for d.py ---

def embed_factory(ctx: commands.Context) -> discord.Embed:
	"""Creates an embed with neutral colour and standard footer."""
	embed = discord.Embed(timestamp=datetime.utcnow(), colour=colours.neutral)
	embed.set_footer(text=str(ctx.author), icon_url=str(ctx.author.avatar_url))
	return embed


def error_embed_factory(ctx: commands.Context, exception: Exception, debug_mode: bool) -> discord.Embed:
	"""Creates an Error embed."""
	if debug_mode:
		fmtd_ex = traceback.format_exception(exception.__class__, exception, exception.__traceback__)
	else:
		fmtd_ex = traceback.format_exception_only(exception.__class__, exception)
	embed = embed_factory(ctx)
	embed.title = "⚠️ Error"
	embed.description = "```\n" + "\n".join(fmtd_ex) + "```"
	embed.colour = colours.bad
	return embed


async def add_react(msg: discord.Message, react: Union[Emoji, Reaction, PartialEmoji, str]):
	try:
		await msg.add_reaction(react)
	except discord.Forbidden:
		idpath = (f"{msg.guild.id}/" if msg.guild else "") + str(msg.channel.id)
		print(f"[!!] Missing permissions to add reaction in '{idpath}'!")


async def react_interactive_message(
		bot: discord.Client,
		msg: discord.Message,
		react: Dict[Union[Emoji, PartialEmoji, str], Coroutine[Any, Any, Union[bool, Tuple[bool, Any]]]],
		timeout=30, caller=None, state: Any=None
	):
	"""
		Adds in responsive reaction emote controls to the message

		Arguments:
			bot: The bot client object
			msg: The msg to add reactions to
			react: A dictionary of emojis and their corresponding callbacks, callbacks have a signature async def callback(*args) -> Union[bool, Tuple[bool, Any]] where the bool is whether to keep responding to new emotes, or terminate the loop
			timeout: How long to wait until timeout
			caller: The user that is this message for, makes only their reactions count, None makes any reaction count
			state: A variable to keep track of data related to the message, passed as the second argument to the callback, can be changed by a callback through returning a tuple (bool, new_state)
	"""
	def check(reaction, user):
		if caller:
			return user == caller and str(reaction.emoji) in react
		else:
			return user != msg.author and str(reaction.emoji) in react
	
	for k in react:
		await msg.add_reaction(k)

	while True:
		try:
			reaction, user = await bot.wait_for("reaction_add", check=check, timeout=timeout)
		except asyncio.TimeoutError:
			break
		try:
			await msg.remove_reaction(reaction, user)
		except discord.Forbidden:
			pass
		
		status = await react[reaction.emoji](msg, state)
		
		# Simple stateless API
		if isinstance(status, bool):
			if not status:
				break
		else:
			# User wishes to use the stateful API
			if not status[0]:
				break
			try:
				state = status[1]
			except IndexError:
				pass

	try:
		await msg.clear_reactions()
	except HTTPException:
		pass
	except discord.Forbidden:
		pass

# --- Helper functions (other) ---

"""Borrowed from wikipedia"""
def is_prime(n: int) -> bool:
	"""Primality test using 6k+-1 optimization."""
	if n <= 3:
		return n > 1
	if n % 2 == 0 or n % 3 == 0:
		return False
	i = 5
	while i * i <= n:
		if n % i == 0 or n % (i + 2) == 0:
			return False
		i += 6
	return True

def factorize(n: int) -> Generator[Tuple[int, int], None, None]:
	"""
		Args: n - an integer
		Returns: A generator of tuples (p, n) where p is the prime and n is the multiplicity, sorted by p
		Remarks: When n is 0 then an empty generator is returned
	"""
	if n == 0:
		return
	if n < 0:
		n = -n
	
	divisions = 0
	while n % 2 == 0:
		divisions += 1
		n /= 2
	if divisions > 0:
		yield (2, divisions)
	
	# avoid a worst-case scenario for large n
	if n > 65336:
		if is_prime(n):
			yield (n, 1)
			return

	divisor = 3
	while divisor <= n:
		divisions = 0
		while n % divisor == 0:
			divisions += 1
			n /= divisor
		if divisions > 0:
			yield (divisor, divisions)
		divisor += 2
	return

def is_square(n):
	if n < 0:
		return False
	if n <= 1:
		return True
	x, y = 1, n
	while x + 1 < y:
		mid = (x+y)//2
		if mid**2 < n:
			x = mid
		else:
			y = mid
	return n == x*x or n == (x+1)*(x+1)

def is_cube(n):
	if n < 0:
		n = -n
	if n <= 1:
		return True
	x, y = 1, n
	while x + 1 < y:
		mid = (x+y)//2
		if mid**3 < n:
			x = mid
		else:
			y = mid
	return n == x*x*x or n == (x+1)*(x+1)*(x+1)

# --- Checks ---

async def check_if_owner(ctx: commands.Context):
	if ctx.author.id in settings.OWNERS:
		return True
	raise commands.NotOwner
