import io
import os
import textwrap
import traceback
import subprocess
from contextlib import redirect_stdout
from time import time
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.enums import ParseMode
from . import app, dev_filter

namespaces = {}

def namespace_of(chat_id, message, bot, app):
    if chat_id not in namespaces:
        namespaces[chat_id] = {
            "__builtins__": globals()["__builtins__"],
            "bot": bot,
            "m": message,
            "from_user": message.from_user,
            "chat": message.chat,
            "_": app,
        }
    return namespaces[chat_id]

async def send(code, output, bot, message, time_taken=None):
    if output is None:
        output = "No output returned."

    reply_markup = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("⏳ Time", callback_data=f"time_{time_taken}"),
                InlineKeyboardButton("🗑 Close", callback_data="close"),
            ]
        ]
    )

    if len(output) > 2000:
        with io.BytesIO(str.encode(output)) as out_file:
            out_file.name = "output.txt"
            await bot.send_document(
                chat_id=message.chat.id,
                document=out_file,
                reply_to_message_id=message.id,
                reply_markup=reply_markup,
            )
    else:
        message_text = (
            f"**CODE**\n```\n{code}\n```\n\n**OUTPUT**\n```\n{output}\n```"
        )
        await bot.send_message(
            chat_id=message.chat.id,
            text=message_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup,
            reply_to_message_id=message.id
        )

@app.on_message(filters.command(["e", "ev", "eva", "eval"]) & dev_filter)
async def evaluate(client, message):
    start_time = time()
    result = await do(eval, client, message)
    time_taken = time() - start_time
    await send(message.text.split(" ", 1)[-1], result, client, message, time_taken)

@app.on_message(filters.command(["x", "ex", "exe", "exec", "py"]) & dev_filter)
async def execute(client, message):
    start_time = time()
    result = await do(exec, client, message)
    time_taken = time() - start_time
    await send(message.text.split(" ", 1)[-1], result, client, message, time_taken)

def cleanup_code(code):
    if code.startswith("```") and code.endswith("```"):
        return "\n".join(code.split("\n")[1:-1])
    return code.strip("` \n")

async def do(func, client, message):
    content = message.text.split(" ", 1)[-1]
    body = cleanup_code(content)
    env = namespace_of(message.chat.id, message, client)

    # Check if the command is pip install
    if body.startswith("pip install"):
        try:
            result = subprocess.run(body.split(), capture_output=True, text=True)
            return result.stdout if result.returncode == 0 else result.stderr
        except Exception as e:
            return f"Error: {str(e)}"

    os.chdir(os.getcwd())
    with open("temp.txt", "w") as temp:
        temp.write(body)

    stdout = io.StringIO()
    to_compile = f'async def func():\n{textwrap.indent(body, "  ")}'

    try:
        exec(to_compile, env)
    except Exception as e:
        return f"{e.__class__.__name__}: {e}"

    func = env["func"]

    try:
        with redirect_stdout(stdout):
            func_return = await func()
    except Exception as e:
        value = stdout.getvalue()
        return f"{value}{traceback.format_exc()}"
    else:
        value = stdout.getvalue()
        result = None
        if func_return is None:
            if value:
                result = f"{value}"
            else:
                try:
                    result = f"{repr(eval(body, env))}"
                except:
                    pass
        else:
            result = f"{value}{func_return}"
        if result:
            return result

@app.on_message(filters.command("clearlocals") & dev_filter)
async def clear(client, message):
    global namespaces
    if message.chat.id in namespaces:
        del namespaces[message.chat.id]
    await send("Cleared locals.", "", client, message)

@app.on_callback_query(filters.regex(r"time_(\d+(\.\d+)?)"))
async def show_time(client, callback_query):
    time_taken = callback_query.data.split("_")[1]
    await callback_query.answer(f"Time taken: {time_taken} seconds", show_alert=True)

@app.on_callback_query(filters.regex("close"))
async def close_message(client, callback_query):
    await callback_query.message.delete()

@app.on_message(filters.command("sh") & dev_filter)
async def shell_command(_, m):
    if len(m.text.split()) == 1:
        return await m.reply("Give me a command to execute.")
    cmd = m.text[4:]
    try:
        result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        output = result.stdout + result.stderr
        if len(output) == 0:
            output = "Command executed successfully, but there is no output."
        if len(output) > 4096:
            with open("output.txt", "w+") as o:
                o.write(output)
            await m.reply_document("output.txt")
        else:
            await m.reply(f"**Command:**\n`{cmd}`\n\n**Output:**\n```\n{output}\n```")
    except Exception as e:
        await m.reply(f"An error occurred:\n`{e}`")