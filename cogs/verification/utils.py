import re
import smtplib
from email.message import EmailMessage

import config
import discord

from main import ProjectHyperlink
from utils.utils import generateID


async def authenticate(
    roll: str,
    name: str,
    email: str,
    bot: ProjectHyperlink,
    author: discord.Member,
    channel_id: int,
    send_message,
) -> bool:
    """Authenticate a given Disord user by verification through email."""
    otp = generateID(seed="01234567890123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ")

    # Creating the email
    msg = EmailMessage()
    msg["Subject"] = f"Verification of {author} in {author.guild}"
    msg["From"] = config.email
    msg["To"] = email

    variables = {
        "{$user}": name,
        "{$otp}": otp,
        "{$guild}": author.guild.name,
        "{$channel}": "https://discord.com/channels/"
        + f"{author.guild.id}/{channel_id}",
    }
    with open("utils/verification.html") as f:
        html = f.read()
    html = re.sub(r"({\$\w+})", lambda x: variables[x.group(0)], html)
    msg.set_content(html, subtype="html")

    # Sending the email
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(config.email, config.password_token)
        smtp.send_message(msg)

    def check(msg: discord.Message):
        return msg.author == author and msg.channel.id == channel_id

    while True:
        message: discord.Message = await bot.wait_for("message", check=check)
        content = message.content
        if otp == content:
            break

        await send_message(
            f"`{content}` is incorrent. Please try again with the correct OTP."
        )

    old_user_id = await bot.pool.fetchval(
        "SELECT discord_id FROM student WHERE roll_number = $1", roll
    )

    await bot.pool.execute(
        """
        UPDATE
            student
        SET
            discord_id = $1,
            is_verified = true
        WHERE
            roll_number = $2
        """,
        author.id,
        roll,
    )

    # TODO: Kick old account from affiliated servers

    return True