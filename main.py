import os
import asyncio
from dotenv import load_dotenv
from pyrogram import Client, errors
from pyrogram.types import (
    Dialog,
    Chat,
    ForumTopic,
    Message,
)
from pyrogram.raw.functions.channels import ToggleForum
from pyrogram.raw.base import InputChannel


import config

load_dotenv()
api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")


async def get_chat_by_title(app: Client, chat_name: str) -> Chat:
    dialog: Dialog
    async for dialog in app.get_dialogs():
        chat: Chat = dialog.chat
        if isinstance(chat.title, str) and chat_name == chat.title:
            return chat


async def get_or_create_my_private_supergroup(app: Client, chat_name: str) -> Chat:
    my_chat: Chat = await get_chat_by_title(app, chat_name)
    if my_chat:
        # Get my chat
        return my_chat
    else:
        # Create my chat
        my_chat: Chat = await app.create_supergroup(chat_name)
        peer: InputChannel = await app.resolve_peer(my_chat.id)
        await app.invoke(ToggleForum(channel=peer, enabled=True, tabs=True))
        return my_chat


async def get_messages_source_topic(
    app: Client, src_chat_id: int, src_topic_id: int
) -> list[Message]:
    message_list = []
    # Get messages from source topic
    message: Message
    async for message in app.search_messages(src_chat_id, thread_id=src_topic_id):
        message_list.append(message)
    return message_list


async def clone_content_forum_topic(
    app: Client,
    src_chat_id: int,
    messages: list[Message],
    my_chat_id: int,
    my_topic_id: int,
    temp_dir_path,
):
    if not temp_dir_path:
        temp_dir_path = "temp_media"
        os.makedirs(temp_dir_path, exist_ok=True)

    total = len(messages)

    for i, msg in enumerate(messages, start=1):
        try:
            msg = await app.get_messages(chat_id=src_chat_id, message_ids=msg.id)

            # Link button
            try:
                url = msg.reply_markup.inline_keyboard[0][0].url
                msg.text += url
            except:
                pass

            # Text
            if msg.text:
                await app.send_message(
                    chat_id=my_chat_id,
                    text=msg.text,
                    entities=msg.entities or None,
                    message_thread_id=my_topic_id,
                )

            # Photo
            elif msg.photo:
                file_path = await app.download_media(msg, file_name=temp_dir_path)
                ext = os.path.splitext(file_path)[1].lower()
                if ext not in (".jpg", ".jpeg", ".png"):
                    new_path = file_path + ".jpg"
                    os.rename(file_path, new_path)
                    file_path = new_path
                await app.send_photo(
                    chat_id=my_chat_id,
                    photo=file_path,
                    caption=msg.caption or "",
                    message_thread_id=my_topic_id,
                )
                os.remove(file_path)

            # Video
            elif msg.video:
                filename = msg.video.file_name or "video.mp4"
                file_path = await app.download_media(
                    msg, file_name=os.path.join(temp_dir_path, filename)
                )
                duration = getattr(msg.video, "duration", 0)
                await app.send_video(
                    chat_id=my_chat_id,
                    video=file_path,
                    caption=msg.caption or "",
                    duration=duration,
                    message_thread_id=my_topic_id,
                )
                os.remove(file_path)

            # Audio, voice
            elif msg.audio or msg.voice:
                filename = (msg.audio.file_name if msg.audio else None) or "voice.ogg"
                file_path = await app.download_media(
                    msg, file_name=os.path.join(temp_dir_path, filename)
                )
                await app.send_voice(
                    chat_id=my_chat_id,
                    voice=file_path,
                    caption=msg.caption or "",
                    message_thread_id=my_topic_id,
                )
                os.remove(file_path)

            # Document
            elif msg.document:
                filename = msg.document.file_name or "document.bin"
                file_path = await app.download_media(
                    msg, file_name=os.path.join(temp_dir_path, filename)
                )
                await app.send_document(
                    chat_id=my_chat_id,
                    document=file_path,
                    caption=msg.caption or "",
                    message_thread_id=my_topic_id,
                )
                os.remove(file_path)

            # Progres
            progress = (i / total) * 100
            print(f"\Progres: {progress:.1f}%", end="")

            await asyncio.sleep(0.3)

        # FloodWait - wait
        except errors.FloodWait as e:
            print(f"\n⏳ FloodWait: wait {e.value} seconds...")
            await asyncio.sleep(e.value + 1)
            messages.insert(i, msg)

        # Error
        except Exception as e:
            print(f"\nError {msg.id}: {e}")

    print("\nDone")

    # Clear temp dir
    try:
        for f in os.listdir(temp_dir_path):
            os.remove(os.path.join(temp_dir_path, f))
    except Exception:
        pass


async def main():
    app = Client("my_account", api_id=api_id, api_hash=api_hash)
    await app.start()

    # Get source chat
    src_chat = await get_chat_by_title(app, config.SOURCE_CHAT_NAME)

    # Create my supergroup
    my_chat: Chat = await get_or_create_my_private_supergroup(app, config.MY_CHAT_NAME)

    # Get topics
    src_topic: ForumTopic
    async for src_topic in app.get_forum_topics(src_chat.id):

        # Check list need topics
        if config.LIST_TOPIC:
            if not src_topic.title in config.LIST_TOPIC:
                continue

        # Get my topic dict
        my_topic_dict: dict[ForumTopic] = {}
        async for my_topic in app.get_forum_topics(my_chat.id):
            my_topic_dict.update({my_topic.title: my_topic})

        # Check my group has source topic title
        if src_topic.title in my_topic_dict.keys():
            my_topic = my_topic_dict[src_topic.title]
        else:
            my_topic: ForumTopic = await app.create_forum_topic(
                my_chat.id, src_topic.title
            )

        # Get messages from source topic
        src_topic_message_list = []
        message: Message
        async for message in app.search_messages(src_chat.id, thread_id=src_topic.id):
            src_topic_message_list.append(message)

        # Sort in chronological order
        src_topic_message_list.reverse()

        # Delete messages service
        for message in src_topic_message_list[:]:
            if message.service:
                src_topic_message_list.remove(message)

        # Copy messages, links, videos, photos, documents
        print(f"Topic.title: {src_topic.title}")
        await clone_content_forum_topic(
            app,
            src_chat.id,
            src_topic_message_list,
            my_chat.id,
            my_topic.id,
            config.TEMP_DIR_PATH,
        )

    await app.stop()


if __name__ == "__main__":
    asyncio.run(main())
