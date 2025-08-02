import discord
from discord.ext import commands
import random
import io
import os

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

def ascii_to_numeric_slash(text):
    result = []
    for char in text:
        ascii_val = ord(char)
        parts = []
        while ascii_val > 0:
            chunk = random.randint(1, min(90, ascii_val))
            parts.append(str(chunk))
            ascii_val -= chunk
        random.shuffle(parts)
        result.append("/".join(parts))
    return "/".join(result)

def generate_lua_wrapper(obfuscated_data):
    return f'''
return(function()
    local obf = "{obfuscated_data}"
    local function decode(s)
        local result = ""
        for chunk in string.gmatch(s, "[^/]+") do
            result = result .. string.char(tonumber(chunk))
        end
        return result
    end
    loadstring(decode(obf))()
end)()
'''

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash commands")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

@bot.tree.command(name="obfuscate", description="Obfuscate Luau code or file")
@discord.app_commands.describe(
    code="Luau code to obfuscate",
    file="Lua or txt file to obfuscate"
)
async def slash_obfuscate(interaction: discord.Interaction, code: str = None, file: discord.Attachment = None):
    if code is None and file is None:
        await interaction.response.send_message("Please provide code or a `.lua`/`.txt` file.", ephemeral=True)
        return

    if file:
        if not file.filename.endswith((".lua", ".txt")):
            await interaction.response.send_message("File must be `.lua` or `.txt`.", ephemeral=True)
            return
        await interaction.response.defer()
        file_bytes = await file.read()
        code_text = file_bytes.decode("utf-8")
    else:
        code_text = code
        await interaction.response.defer()

    obfuscated = ascii_to_numeric_slash(code_text)
    lua_code = generate_lua_wrapper(obfuscated)

    if file:
        obfuscated_file = discord.File(
            fp=io.BytesIO(lua_code.encode()),
            filename=f"PepperOBF_{file.filename}"
        )
        await interaction.followup.send("✅ Obfuscation complete. Here's your file:", file=obfuscated_file)
    else:
        # Send obfuscated code snippet (max 1900 chars to avoid Discord message limit)
        await interaction.followup.send(f"```lua\n{lua_code[:1900]}\n```")

@bot.tree.command(name="help", description="Show PepperOBF help")
async def slash_help(interaction: discord.Interaction):
    help_text = (
        "**PepperOBF Commands:**\n"
        "`/obfuscate code:<code>` - Obfuscate Luau code inline.\n"
        "`/obfuscate file:<file>` - Obfuscate a Lua or txt file.\n"
        "`!obfuscate <code>` - Obfuscate Luau code inline.\n"
        "`!help` or `/help` - Show this help message.\n"
        "`/about` - Info about PepperOBF bot."
    )
    await interaction.response.send_message(help_text)

@bot.tree.command(name="about", description="About PepperOBF bot")
async def slash_about(interaction: discord.Interaction):
    about_text = (
        "**PepperOBF v2.2.2**\n"
        "Made by azxer_manalt.\n"
        "Obfuscates `.lua` or `.txt` files and inline code.\n"
        "Includes decoder function in output Lua script."
    )
    await interaction.response.send_message(about_text)

@bot.command()
async def obfuscate(ctx, *, code: str = None):
    if code:
        obfuscated = ascii_to_numeric_slash(code)
        lua_code = generate_lua_wrapper(obfuscated)
        await ctx.send(f"```lua\n{lua_code[:1900]}\n```")
    else:
        await ctx.send("Please provide code to obfuscate.")

@bot.command()
async def help(ctx):
    help_text = (
        "**PepperOBF Commands:**\n"
        "`!obfuscate <code>` - Obfuscate Luau code inline.\n"
        "`!help` or `/help` - Show this help message.\n"
        "`/about` - Info about PepperOBF bot."
    )
    await ctx.send(help_text)

def read_token_from_file(filename="config.txt"):
    try:
        with open(filename, "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        print(f"Error: {filename} not found!")
        return None

TOKEN = read_token_from_file()
if TOKEN is None:
    exit("Bot token not found in config.txt. Exiting.")

bot.run(TOKEN)
