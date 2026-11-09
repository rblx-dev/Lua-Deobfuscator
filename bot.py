import os
import io
import logging

import discord
from discord import app_commands

from deobfuscator import deobfuscate_lua

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s"
)

TOKEN = os.environ.get("DISCORD_TOKEN")

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

MAX_LUA_SIZE = 8 * 1024 * 1024  # 8 MB


@tree.command(
    name="deobfuscate",
    description="Upload a Lua file and receive a statically deobfuscated version."
)
@app_commands.describe(
    file="The .lua file you want to deobfuscate"
)
async def deobfuscate(
    interaction: discord.Interaction,
    file: discord.Attachment
):
    await interaction.response.defer(ephemeral=True)

    if not file.filename.lower().endswith(".lua"):
        await interaction.followup.send(
            "Please upload a `.lua` file."
        )
        return

    if file.size > MAX_LUA_SIZE:
        await interaction.followup.send(
            "That file is too large. The limit is 8 MB."
        )
        return

    try:
        raw = await file.read()
        source = raw.decode("utf-8")
    except UnicodeDecodeError:
        source = raw.decode("utf-8", errors="replace")
    except Exception:
        await interaction.followup.send(
            "I could not read that file. Please upload it again."
        )
        return

    try:
        cleaned, report = deobfuscate_lua(source)
    except Exception as error:
        logging.exception("Deobfuscation failed")
        await interaction.followup.send(
            f"Deobfuscation failed:\n```text\n{str(error)[:1000]}\n```"
        )
        return

    output = io.BytesIO(cleaned.encode("utf-8"))
    output.seek(0)

    result_file = discord.File(
        fp=output,
        filename=f"deobfuscated_{file.filename}"
    )

    report_text = report[:1800] if report else "No changes detected."

    await interaction.followup.send(
        content=(
            "**Deobfuscation complete**\n"
            f"```text\n{report_text}\n```"
        ),
        file=result_file
    )


@tree.command(name="ping", description="Check whether the bot is online.")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(
        "Online and ready to deobfuscate Lua files.",
        ephemeral=True
    )


@client.event
async def on_ready():
    try:
        await tree.sync()
        logging.info("Slash commands synced.")
    except Exception:
        logging.exception("Failed to sync slash commands")

    logging.info(f"Bot is online as {client.user}")


if __name__ == "__main__":
    if not TOKEN:
        raise SystemExit(
            "DISCORD_TOKEN environment variable is missing."
        )

    client.run(TOKEN)
