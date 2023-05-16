from discord import (
    Embed,
    Client,
    Object,
    Member,
    Intents,
    VoiceState,
    app_commands,
)

import os
import time
import datetime
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

from utilities import createLogger


load_dotenv(verbose=True)

MY_GUILD = Object(id=int(os.getenv("GUILD_ID")))
database = AsyncIOMotorClient(os.getenv("DATABASE_URL"))["HeeKyung"]

state = {}


class HeeKyung(Client):
    def __init__(self):
        super().__init__(
            intents=Intents.all(),
        )
        self.logger = createLogger("discord", 20)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        self.tree.copy_global_to(guild=MY_GUILD)
        await self.tree.sync(guild=MY_GUILD)

    async def on_ready(self):
        self.logger.info(f"Logged in as {self.user} (ID: {self.user.id})")

    async def on_message(self, message):
        if message.author == self.user:
            return

    async def on_voice_state_update(
        self, member: Member, before: VoiceState, after: VoiceState
    ):
        if (before.channel or after.channel) != self.get_channel(
            int(os.getenv("WORKING_CHANNEL_ID"))
        ):
            return
        if before.channel is None and after.channel is not None:
            state[str(member.id)] = time.time()
        elif before.channel is not None and after.channel is None:
            if state.get(str(member.id)) is None:
                return
            if time.time() - state[str(member.id)] < 10:
                del state[str(member.id)]
                return
            seconds = int(time.time() - state[str(member.id)])
            hours = seconds // 3600
            minutes = seconds // 60
            await self.get_channel(int(os.getenv("WORKING_LOG_CHANNEL_ID"))).send(
                embed=Embed(
                    title="📔 개발 기록",
                    description=f"대상 : {member.mention}\n" f"시간 : {hours}시간 {minutes}분",
                    color=member.color,
                )
            )
            await database["working"].insert_one(
                {
                    "user": {
                        "id": member.id,
                        "name": str(member),
                    },
                    "time": f"{hours}시간 {minutes}분 {seconds - hours * 3600}초",
                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
            )
            del state[str(member.id)]


client = HeeKyung()


if __name__ == "__main__":
    client.run(os.getenv("TOKEN"))
