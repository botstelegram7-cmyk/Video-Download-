"""
Reactions Plugin — Bot reacts to EVERY message (text, photo, video,
sticker, document, audio, etc.) in both private chats AND groups/supergroups.
Uses Pyrogram raw API for Pyrogram 2.0.106 compatibility.
"""
import random
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.raw import functions, types as raw_types
from pyrogram.errors import (
    ReactionInvalid, ChatAdminRequired, UserNotParticipant,
    FloodWait, MessageNotModified, PeerIdInvalid
)
from client import app
from config import REACTION_EMOJIS, REACTIONS_ENABLED


@app.on_message(
    (filters.private | filters.group | filters.supergroup)
    & ~filters.outgoing
    & ~filters.service
)
async def react_to_message(client: Client, msg: Message):
    """React to every incoming message."""
    if not REACTIONS_ENABLED:
        return
    if not msg.from_user:
        return  # ignore channel posts with no sender

    emoji = random.choice(REACTION_EMOJIS)
    await asyncio.sleep(random.uniform(0.3, 1.2))   # slight natural delay

    try:
        await client.invoke(
            functions.messages.SendReaction(
                peer=await client.resolve_peer(msg.chat.id),
                msg_id=msg.id,
                reaction=[raw_types.ReactionEmoji(emoticon=emoji)],
                big=False,
            )
        )
    except FloodWait as e:
        await asyncio.sleep(e.value)
    except (ReactionInvalid, ChatAdminRequired, UserNotParticipant,
            MessageNotModified, PeerIdInvalid):
        pass   # silently skip unsupported chats / permissions
    except Exception:
        pass   # never crash on reaction failure
