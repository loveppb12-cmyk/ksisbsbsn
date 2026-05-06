import asyncio
from datetime import datetime, timedelta

from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import RPCError

# ---------- CONFIGURATION ----------
API_ID = 20284828
API_HASH = "a980ba25306901d5c9b899414d6a9ab7"
STRING_SESSION = "BQE1hZwAp_OoAIx-rGQFLFol4g41WGiIyUNB8PhbqQXA0sMiGI1HKEt-dN9ihQ_CGVKh0u5a_um5LDZivezqhd2DoJvHsR_HIdLohL7T4pG0K6uhCTEZd9P9_GIqBxzx8OmpHDh0vJXxyu1UrFMuHUtenfxXdD1VYSU8cgqjN9CCeDqC4wzKa4rctVwYUlPxz49DSU30ffjAz88l6uHIChG-V5dPmVMsoYjE04gmC4VWbGcLVb6f5sKSeLgoFL2AqeakYDWxZ6GCMEgRsWWjVCOmHwdxJpWHeD7v6gRbgoKOgdSVpLX2A01f7mGXzfOqviGGF2mpl2KQAywhaG1Sl_E-GX149AAAAAIJRzvaAA"

# Time in seconds after which bot messages will be deleted
DELAY_SECONDS = 100

# ---------- END CONFIGURATION ----------

# Create client - Pyrogram v2+ compatible way
app = Client(
    name="userbot_session",
    api_id=API_ID,
    api_hash=API_HASH,
    session_string=STRING_SESSION  # This is correct for Pyrogram v2+
)

# Store pending deletion tasks
pending_deletions = {}

async def delayed_delete(chat_id: int, message_id: int, delete_at: datetime):
    """Wait and delete a specific message"""
    now = datetime.now()
    wait_seconds = (delete_at - now).total_seconds()
    if wait_seconds > 0:
        await asyncio.sleep(wait_seconds)
    try:
        await app.delete_messages(chat_id, message_id)
        print(f"[✓] Deleted bot message {message_id} in chat {chat_id}")
    except RPCError as e:
        print(f"[✗] RPC Error deleting message {message_id}: {e}")
    except Exception as e:
        print(f"[✗] Failed to delete message {message_id}: {e}")

@app.on_message(filters.group & ~filters.me)
async def handle_bot_messages(client: Client, message: Message):
    """Detect bot messages and schedule deletion"""
    # Check if message is from a bot
    if message.from_user and message.from_user.is_bot:
        chat_id = message.chat.id
        message_id = message.id
        
        # Schedule deletion after DELAY_SECONDS
        delete_at = datetime.now() + timedelta(seconds=DELAY_SECONDS)
        
        # Create unique key for this message
        key = f"{chat_id}_{message_id}"
        
        # Cancel existing task if any (shouldn't happen)
        if key in pending_deletions:
            pending_deletions[key].cancel()
        
        # Create and store deletion task
        task = asyncio.create_task(delayed_delete(chat_id, message_id, delete_at))
        pending_deletions[key] = task
        
        # Clean up reference when done
        task.add_done_callback(lambda t: pending_deletions.pop(key, None))
        
        print(f"[→] Scheduled bot message {message_id} for deletion in {DELAY_SECONDS}s")

@app.on_message(filters.command("start") & filters.private)
async def start_command(client: Client, message: Message):
    await message.reply(
        "🤖 **UserBot Active**\n\n"
        "I will delete messages from **bots** in any group where I am an admin with 'Delete Messages' permission.\n\n"
        f"⏱️ Deletion delay: {DELAY_SECONDS} seconds\n"
        "✅ Just add me to a group as admin and I'll start working automatically."
    )

@app.on_message(filters.command("ping") & filters.private)
async def ping_command(client: Client, message: Message):
    start = datetime.now()
    msg = await message.reply("🏓 Pong!")
    end = datetime.now()
    latency = (end - start).total_seconds() * 1000
    await msg.edit(f"🏓 Pong!\nLatency: `{latency:.2f} ms`")

async def main():
    print("[START] UserBot is starting...")
    print(f"[INFO] Will delete bot messages after {DELAY_SECONDS} seconds")
    print("[INFO] Make sure the userbot is admin in target groups with 'Delete messages' right")
    
    try:
        # Start the client
        await app.start()
        
        # Get bot info
        me = await app.get_me()
        print(f"[✓] Logged in as: {me.first_name} (@{me.username})")
        print(f"[✓] User ID: {me.id}")
        print("[INFO] UserBot is now running. Press Ctrl+C to stop.")
        
        # Keep the bot running
        await asyncio.Event().wait()
        
    except Exception as e:
        print(f"[ERROR] Failed to start: {e}")
        raise
    finally:
        await app.stop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[STOP] UserBot stopped by user")
    except Exception as e:
        print(f"[ERROR] {e}")
