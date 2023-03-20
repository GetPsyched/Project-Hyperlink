import discord
import traceback

from cogs.verification.utils import authenticate, post_verification_handler
from main import ProjectHyperlink

GUILD_IDS = {
    904633974306005033: 0,
    783215699707166760: 2024,
    915517972594982942: 2025,
}


class VerificationView(discord.ui.View):
    def __init__(self, label: str, bot: ProjectHyperlink, fmv):
        super().__init__()

        button = VerificationButton(label, bot, fmv)
        self.add_item(button)


class VerificationButton(discord.ui.Button):
    def __init__(self, label, bot: ProjectHyperlink, fmv, **kwargs):
        super().__init__(label=label, style=discord.ButtonStyle.green, **kwargs)
        self.bot = bot
        self.fmv = fmv

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(VerificationModal(self.bot, self.fmv))


class VerificationModal(discord.ui.Modal, title="Verification"):
    roll = discord.ui.TextInput(
        label="Roll Number",
        placeholder="12022005",
        max_length=8,
        min_length=8,
    )

    def __init__(self, bot: ProjectHyperlink, fmv):
        super().__init__()
        self.bot = bot
        self.fmv = fmv

    async def on_submit(self, interaction: discord.Interaction):
        # To please linter gods:
        assert isinstance(interaction.user, discord.Member)
        assert interaction.channel_id is not None
        assert self.roll.value is not None

        member = interaction.user

        student: dict[str, str] = await self.bot.pool.fetchrow(
            f"""
            SELECT
                roll_number,
                section,
                name,
                email,
                batch,
                hostel_id
            FROM
                student
            WHERE
                roll_number = $1
            """,
            self.roll.value,
        )
        if not student:
            await interaction.response.send_message(
                self.fmv("roll-notfound", {"roll": self.roll.value}),
                ephemeral=True,
            )
            return

        if (
            GUILD_IDS[member.guild.id] != 0
            and GUILD_IDS[member.guild.id] != student["batch"]
        ):
            message = self.fmv("incorrect-guild", {"batch": student["batch"]})
            await interaction.response.send_message(message, ephemeral=True)
            return

        await interaction.response.send_message(
            self.fmv("email-sent", {"email": student["email"]}),
            ephemeral=True,
        )

        verified = await authenticate(
            self.roll.value,
            student["name"],
            student["email"],
            self.bot,
            member,
            interaction.channel_id,
            interaction.followup.send,
        )
        if verified is False:
            return

        await interaction.followup.send(
            self.fmv("verification-success", {"mention": member.mention})
        )

        await post_verification_handler(member, student, self.bot.pool)

    async def on_error(
        self, interaction: discord.Interaction, error: Exception
    ) -> None:
        await interaction.followup.send("Oops! Something went wrong.", ephemeral=True)

        traceback.print_exception(type(error), error, error.__traceback__)
