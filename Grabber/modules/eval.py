import io
import os
import textwrap
import traceback
from contextlib import redirect_stdout

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.enums import ParseMode
from . import app, sudo_filter
namespaces = {}

def namespace_of(chat_id, message, bot):
    if chat_id not in namespaces:
        namespaces[chat_id] = {
            "__builtins__": globals()["__builtins__"],
            "bot": bot,
            "message": message,
            "from_user": message.from_user,
            "chat": message.chat,
        }
    return namespaces[chat_id]

def log_input(message):
    user = message.from_user.id
    chat = message.chat.id
    print(f"IN: {message.text} (user={user}, chat={chat})")

async def send(msg, bot, message):
    if len(str(msg)) > 2000:
        with io.BytesIO(str.encode(msg)) as out_file:
            out_file.name = "output.txt"
            await bot.send_document(
                chat_id=message.chat.id,
                document=out_file,
                reply_to_message_id=message.id
            )
    else:
        print(f"OUT: '{msg}'")
        await bot.send_message(
            chat_id=message.chat.id,
            text=f"```\n{msg}\n```",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Close", callback_data="close")]]
            ),
            reply_to_message_id=message.id
        )

@app.on_message(filters.command(["e", "ev", "eva", "eval"]) & sudo_filter)
async def evaluate(client, message):
    await send(await do(eval, client, message), client, message)

@app.on_message(filters.command(["x", "ex", "exe", "exec", "py"]) & sudo_filter)
async def execute(client, message):
    await send(await do(exec, client, message), client, message)

def cleanup_code(code):
    if code.startswith("```") and code.endswith("```"):
        return "\n".join(code.split("\n")[1:-1])
    return code.strip("` \n")

async def do(func, client, message):
    log_input(message)
    content = message.text.split(" ", 1)[-1]
    body = cleanup_code(content)
    env = namespace_of(message.chat.id, message, client)

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

@app.on_message(filters.command("clearlocals") & sudo_filter)
async def clear(client, message):
    log_input(message)
    global namespaces
    if message.chat.id in namespaces:
        del namespaces[message.chat.id]
    await send("Cleared locals.", client, message)

@app.on_callback_query(filters.regex("close"))
async def close_message(client, callback_query):
    await callback_query.message.delete()
