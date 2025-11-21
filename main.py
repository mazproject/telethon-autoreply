import os
import asyncio
import time
from telethon import TelegramClient, events

# === Konfigurasi dari Environment Variable ===
api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")
session_name = os.getenv("SESSION_NAME", "auto_reply_session")

auto_reply_message = (
    "Woii! Lagi sibuk banget nih, gak bisa bales dulu. "
    "Nanti kalo udah free, gue balas deh.. "
    "Stay Chill! 😎"
)

RESET_TIME = 10 * 60  # 10 menit

manually_replied_chats = set()
last_interaction = {}
auto_reply_messages = {}

client = TelegramClient(session_name, api_id, api_hash)

@client.on(events.NewMessage(incoming=True))
async def incoming_handler(event):
    if event.out:
        return
    sender = await event.get_sender()
    if sender.bot or not event.is_private:
        return

    chat_id = event.chat_id
    now = time.time()
    last_interaction[chat_id] = now

    if chat_id in manually_replied_chats:
        print(f"Sudah balas manual ke {sender.first_name}, bot diam.")
        return

    msg = await event.respond(auto_reply_message)
    auto_reply_messages.setdefault(chat_id, []).append(msg.id)
    print(f"Auto-reply terkirim ke: {sender.first_name}")

@client.on(events.NewMessage(outgoing=True))
async def outgoing_handler(event):
    chat_id = event.chat_id
    now = time.time()
    last_interaction[chat_id] = now

    if chat_id not in manually_replied_chats:
        manually_replied_chats.add(chat_id)
        print(f"Manual reply terdeteksi di chat {chat_id}.")

        if chat_id in auto_reply_messages:
            try:
                await client.delete_messages(chat_id, auto_reply_messages[chat_id], revoke=True)
                print("Auto-reply dihapus.")
            except Exception as e:
                print(f"Error hapus: {e}")
            auto_reply_messages.pop(chat_id, None)

async def reset_checker():
    while True:
        await asyncio.sleep(60)
        now = time.time()
        for chat_id in list(manually_replied_chats):
            last_time = last_interaction.get(chat_id, 0)
            if now - last_time > RESET_TIME:
                manually_replied_chats.remove(chat_id)
                print("Bot kembali aktif untuk chat:", chat_id)

async def main():
    await client.start()
    print("Bot aktif! Menunggu pesan...")
    client.loop.create_task(reset_checker())
    await client.run_until_disconnected()

client.loop.run_until_complete(main())
