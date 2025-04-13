from pyrogram import Client, filters
from pyrogram.types import Message
from datetime import datetime, timedelta
import time

# Configs
API_ID = 22012880
API_HASH = "5b0e07f5a96d48b704eb9850d274fe1d"
SESSION_STRING = "your_session_string_here"  # ← Paste here

# AFK Data
afk_info = {
    "is_afk": False,
    "reason": "I'm AFK",
    "start_time": None,
    "message_log": []
}

app = Client("my_userbot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)

@app.on_message(filters.command("afk") & filters.me)
async def activate_afk(client: Client, message: Message):
    reason = " ".join(message.command[1:]) if len(message.command) > 1 else "I'm AFK"
    afk_info.update({
        "is_afk": True,
        "reason": reason,
        "start_time": time.time(),
        "message_log": []
    })
    await message.edit(f"🚀 **AFK Mode Activated!**\n📝 Reason: {reason}")

@app.on_message(filters.command("back") & filters.me)
async def disable_afk(client: Client, message: Message):
    if afk_info["is_afk"]:
        afk_duration = str(timedelta(seconds=int(time.time() - afk_info["start_time"])))
        missed_messages = "\n".join(
            f"- [{msg.from_user.first_name}](tg://user?id={msg.from_user.id})"
            for msg in afk_info["message_log"]
        )
        await message.edit(
            f"🎉 **I'm Back!**\n⏳ Was AFK for: `{afk_duration}`\n"
            f"📨 **Missed Messages:**\n{missed_messages if missed_messages else 'None'}"
        )
        afk_info.update({"is_afk": False, "message_log": []})

@app.on_message((filters.private | filters.mentioned) & ~filters.me & ~filters.bot)
async def afk_response(client: Client, message: Message):
    if afk_info["is_afk"]:
        afk_time = str(timedelta(seconds=int(time.time() - afk_info["start_time"])))
        await message.reply(
            f"⏳ **User is AFK** ({afk_time} ago)\n📝 Reason: {afk_info['reason']}",
            quote=True
        )
        afk_info["message_log"].append(message)

if __name__ == "__main__":
    print("Userbot is running...")
    app.run()
