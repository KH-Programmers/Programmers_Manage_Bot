from discord import (
    utils,
    Embed,
    Color,
    Client,
    Object,
    Member,
    Intents,
    VoiceState,
    Interaction,
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
                    "time": f"{hours}시간 {minutes}분 {seconds - hours * 3600 - minutes * 60}초",
                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
            )
            del state[str(member.id)]


client = HeeKyung()


@client.tree.command(name="개발기록", description="( 팀장 전용 명령어 ) 멤버들의 개발 기록을 확인합니다.")
async def accessWorkingLog(interaction: Interaction):
    if (
        utils.get(interaction.guild.roles, id=int(os.getenv("LEADER_ID")))
        not in interaction.user.roles
    ):
        await interaction.response.send_message(
            embed=Embed(
                title="❌ 접근 권한 없음",
                description="이 명령어는 팀장만 사용할 수 있습니다.",
                color=Color.red(),
            ),
            ephemeral=True,
        )
        return
    logWorkingData = await database["working"].find().to_list(length=None)
    if len(logWorkingData) == 0:
        await interaction.response.send_message(
            embed=Embed(
                title="❌ 개발 기록 없음",
                description="아직 개발 기록이 없습니다.",
                color=Color.red(),
            ),
            ephemeral=True,
        )
        return
    embed = Embed(
        title="📔 개발 기록",
        description="",
        color=Color.green(),
    ).set_footer(
        text=f'{len(logWorkingData[:10])} 개를 표시합니다.'
    )
    for data in logWorkingData[:10]:
        embed.add_field(
            name=f"{data['user']['name']} ({data['user']['id']})",
            value=f"⏱️ 시간 : {data['time']}\n📅 일시 : {data['timestamp']}",
        )
    await interaction.response.send_message(embed=embed)



if __name__ == "__main__":
    client.run(os.getenv("TOKEN"))
