from typing import Counter
from discord.ext import commands, tasks
import json
from math import gcd, isqrt
from functools import reduce
from random import random
from util import paths, check_if_owner, factorize, is_square, is_cube


class CounterCog(commands.Cog, name='counting'):
	def __init__(self, bot):
		self.bot = bot
		self.changed = False
		self.update_index.start()

	def cog_unload(self):
		self.update_index.cancel()

	@commands.command("addcan", pass_context=True, description="Adds a can")
	@commands.cooldown(1, 6, commands.BucketType.user)
	async def addcan(self, ctx):
		self.can += 1
		self.changed = True
		modifiers = ""
		factorization = list(factorize(self.can))
		if len(factorization) > 1:
			greatest_common_exponent = reduce(gcd, [n for _,n in factorization])
		else:
			greatest_common_exponent = 1
		if greatest_common_exponent % 2 == 0:
			modifiers += " These cans make a square."
		if greatest_common_exponent % 3 == 0:
			modifiers += " These cans make a cube!"
		if is_square(8*self.can+1):
			if isqrt(8*self.can+1) % 4 == 3:
				modifiers += " These cans make a triangle and a hexagon!!"
			else:
				modifiers += " These cans make a triangle!"
		if greatest_common_exponent > 3:
			modifiers += f" These cans are a {greatest_common_exponent}th power, hope you know how to stack cans in {greatest_common_exponent}D."
		if len(factorization) == 1 and factorization[0][1] == 1:
			modifiers += " These cans are a prime number!!!"
		if self.can % 100 == 69:
			modifiers += " nice."
		if self.can % 1000 == 413:
			modifiers += " Lets me tell you about homestuck."
		await ctx.send(f"You added a can, there are now {self.can} cans.{modifiers}")

	@commands.command("john", pass_context=True, description="Adds, removes, or gives status of johns in the johnverse")
	async def john(self, ctx, *, command = ""):
		message = ""
		if command == "":
			message += "Use john add/kill to add or remove a john\n\n"
		elif command == "add":
			modifier = ""
			if random() < 0.1:
				modifier += "poor little "
			if random() < 0.04:
				modifier += "gay "
			if random() < 0.001:
				modifier += "rare "
			if random() < 0.005:
				modifier += "limited edition "
			if len(modifier) == 0 and random() < 0.1:
				modifier += "completely generic "
			if len(modifier) == 0 and random() < 0.01:
				modifier += "extraordinarily generic "
			message += f"You have successfully added a {modifier}john\n\n"
			self.john_add += 1
			self.changed = True
		elif command == "kill":
			modifier = ""
			bonus_sentence = ""
			if random() < 0.1:
				modifier += "monstrously "
				if random() < 0.8:
					bonus_sentence = " You monster."
			if random() < 0.04:
				modifier += "unimaginably "
				if random() < 0.1:
					bonus_sentence = " I don't even comprehend."
			if random() < 0.005:
				modifier += "full-on jack-noir "
				if random() < 0.3:
					bonus_sentence = " I TOLD YOU ABOUT THE RED MILES JOHN, I TOLD YOU DAWG."
			if len(modifier) == 0 and random() < 0.1:
				modifier += "painlessly "
				if random() < 0.08:
					bonus_sentence = " v-v"
			if len(modifier) == 0 and random() < 0.01:
				modifier += "accidentally "
				if random() < 0.08:
					bonus_sentence = " I don't believe your tales."
			message += f"You have {modifier}killed a john.{bonus_sentence}\n\n"
			self.john_kill += 1
			self.changed = True
		else:
			message += "Uh... I am not sure how to do that, please use john add or john kill\n\n"
		message += f"There are currently {self.john_add - self.john_kill} johns.\n{self.john_add} johns have been added, {self.john_kill} johns have been killed."
		if self.john_add < self.john_kill:
			message += ".. Somehow..."
		await ctx.send(message)

	@tasks.loop(seconds=300)
	async def update_index(self):
		if self.changed:
			self.save()

	def load(self, file = paths.data / "counters/counters.json"):
		with open(file, "r") as fp:
			raw = json.load(fp)
		self.john_add  = raw.get("john_add",  0)
		self.john_kill = raw.get("john_kill", 0)
		self.can = raw.get("can", 0)

	def save(self, file = paths.data / "counters/counters.json"):
		with open(file, "w") as fp:
			json.dump({
				"john_add":  self.john_add,
				"john_kill": self.john_kill,
				"can": self.can
			}, fp)

def setup(bot):
	cog = CounterCog(bot)
	cog.load()
	bot.add_cog(cog)

def teardown(bot): 
	pass
