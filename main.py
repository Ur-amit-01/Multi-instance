from pyrogram import Client, filters, idle
from pyrogram.types import Message
from pyrogram.errors import (
    PhoneNumberInvalid,
    PhoneCodeInvalid,
    PhoneCodeExpired,
    SessionPasswordNeeded,
    PasswordHashInvalid
)
import os
import asyncio

# Bot configuration
API_ID = 22012880  # Replace with your API_ID
API_HASH = "5b0e07f5a96d48b704eb9850d274fe1d"  # Replace with your API_HASH
BOT_TOKEN = "7557297602:AAH6-43MKGE0umypUgeonsfk41wOrsDKCnM"  # Replace with your bot token

# Initialize the bot
app = Client("session_generator_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# User session data storage (in memory, cleared after use)
user_sessions = {}

@app.on_message(filters.command("start") & filters.private)
async def start(client: Client, message: Message):
    await message.reply("""
    **Pyrogram String Session Generator**
    
    Use /generate to start creating your Pyrogram string session.
    
    🔒 *Security Note*:
    - This bot will never store your session permanently
    - All data is deleted after session generation
    - Only use this bot if you trust the source
    """)

@app.on_message(filters.command("generate") & filters.private)
async def generate_session(client: Client, message: Message):
    user_id = message.from_user.id
    user_sessions[user_id] = {"step": "api_id"}
    
    await message.reply("""
    Let's generate your Pyrogram string session!
    
    Please send your **API_ID** (get it from https://my.telegram.org/apps)
    """)

@app.on_message(filters.private & ~filters.command(["start", "generate"]))
async def handle_session_generation(client: Client, message: Message):
    user_id = message.from_user.id
    if user_id not in user_sessions:
        return
    
    current_step = user_sessions[user_id].get("step")
    
    if current_step == "api_id":
        try:
            api_id = int(message.text)
            user_sessions[user_id]["api_id"] = api_id
            user_sessions[user_id]["step"] = "api_hash"
            await message.reply("✅ Got your API_ID. Now please send your **API_HASH**")
        except ValueError:
            await message.reply("⚠️ Please send a valid numeric API_ID")
    
    elif current_step == "api_hash":
        api_hash = message.text.strip()
        if len(api_hash) < 10:  # Basic validation
            await message.reply("⚠️ Please send a valid API_HASH")
            return
            
        user_sessions[user_id]["api_hash"] = api_hash
        user_sessions[user_id]["step"] = "phone_number"
        await message.reply("""
        ✅ Got your API_HASH.
        
        Now please send your **phone number** in international format:
        Example: +1234567890
        """)
    
    elif current_step == "phone_number":
        phone_number = message.text.strip()
        user_sessions[user_id]["phone_number"] = phone_number
        
        # Create a temporary client to generate the session
        temp_client = Client(
            f"user_{user_id}_session",
            api_id=user_sessions[user_id]["api_id"],
            api_hash=user_sessions[user_id]["api_hash"],
            phone_number=phone_number,
            in_memory=True
        )
        
        try:
            await temp_client.connect()
            sent_code = await temp_client.send_code(phone_number)
            
            user_sessions[user_id]["temp_client"] = temp_client
            user_sessions[user_id]["phone_code_hash"] = sent_code.phone_code_hash
            user_sessions[user_id]["step"] = "verification_code"
            
            await message.reply("""
            ✅ Telegram should have sent you a verification code.
            
            Please send that code in the format:
            `1 2 3 4 5` (with spaces between numbers)
            """)
            
        except PhoneNumberInvalid:
            await message.reply("⚠️ Invalid phone number. Please start over with /generate")
            del user_sessions[user_id]
        except Exception as e:
            await message.reply(f"⚠️ Error: {str(e)}\n\nPlease start over with /generate")
            del user_sessions[user_id]
            if 'temp_client' in locals():
                await temp_client.disconnect()
    
    elif current_step == "verification_code":
        verification_code = message.text.strip().replace(" ", "")
        if not verification_code.isdigit():
            await message.reply("⚠️ Please send only numbers (e.g., '1 2 3 4 5')")
            return
            
        temp_client = user_sessions[user_id]["temp_client"]
        phone_code_hash = user_sessions[user_id]["phone_code_hash"]
        
        try:
            # Try to sign in with the verification code
            signed_in = await temp_client.sign_in(
                user_sessions[user_id]["phone_number"],
                phone_code_hash,
                verification_code
            )
            
            # If we get here, sign in was successful
            session_string = await temp_client.export_session_string()
            await send_session_to_saved_messages(client, user_id, session_string)
            await message.reply("✅ Session generated successfully! Check your Saved Messages.")
            
            # Clean up
            await temp_client.disconnect()
            del user_sessions[user_id]
            
        except SessionPasswordNeeded:
            # If 2FA is required, ask for password
            user_sessions[user_id]["step"] = "password"
            await message.reply("""
            🔐 Your account has 2-step verification enabled.
            
            Please send your **password** to continue.
            """)
            
        except PhoneCodeInvalid:
            await message.reply("⚠️ Invalid verification code. Please start over with /generate")
            await temp_client.disconnect()
            del user_sessions[user_id]
        except PhoneCodeExpired:
            await message.reply("⚠️ Verification code expired. Please start over with /generate")
            await temp_client.disconnect()
            del user_sessions[user_id]
        except Exception as e:
            await message.reply(f"⚠️ Error: {str(e)}\n\nPlease start over with /generate")
            await temp_client.disconnect()
            del user_sessions[user_id]
    
    elif current_step == "password":
        password = message.text.strip()
        temp_client = user_sessions[user_id]["temp_client"]
        
        try:
            # Sign in with password
            await temp_client.check_password(password)
            
            # Export and send the session
            session_string = await temp_client.export_session_string()
            await send_session_to_saved_messages(client, user_id, session_string)
            await message.reply("✅ Session generated successfully! Check your Saved Messages.")
            
        except PasswordHashInvalid:
            await message.reply("⚠️ Invalid password. Please try again or start over with /generate")
        except Exception as e:
            await message.reply(f"⚠️ Error: {str(e)}\n\nPlease start over with /generate")
        finally:
            # Clean up
            if user_id in user_sessions:
                if "temp_client" in user_sessions[user_id]:
                    await user_sessions[user_id]["temp_client"].disconnect()
                del user_sessions[user_id]

async def send_session_to_saved_messages(client: Client, user_id: int, session_string: str):
    # Send the session string to user's saved messages
    await client.send_message(
        "me",  # This goes to the user's saved messages
        f"""
        **Pyrogram String Session**
        
        ```{session_string}```
        
        🔒 *Important Security Notes*:
        1. Never share this string with anyone
        2. If compromised, revoke it immediately at https://my.telegram.org/auth
        3. This bot does not store your session
        """,
        disable_web_page_preview=True
    )

if __name__ == "__main__":
    print("Starting session generator bot...")
    app.start()
    idle()
    app.stop()
