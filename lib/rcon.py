import aiomcrcon as mc
from data.secrets import MC_RCON_PASS as PASS
from data.settings import MC_RCON_ADRESS as ADRESS

class RCON():
	"""
	Handler for connection to the minecraft server
	"""
	def __init__(self) -> None:
		self.client = None
		super().__init__()

	async def ensure_client(self):
		if self.client is None:
			self.client = mc.Client(ADRESS, PASS)
			try:
				await self.client.setup()
			except:
				self.client = None
				raise RCONUnavailableException("Could not reach the Minecraft server")

	async def send(self, command):
		await self.ensure_client()
		return await self.client.send_cmd(command)

	def __del__(self):
		if self.client != None:
			self.client.close()

class RCONUnavailableException(Exception):
	def __init__(self, *args: object) -> None:
		super().__init__(*args)
