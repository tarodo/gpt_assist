import asyncio
import logging
import os
import sqlite3

from openai import OpenAI, AsyncOpenAI
from telegram import ForceReply, Update, User
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from gpt import retrieve_assistant, async_retrieve_assistant

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

conn = sqlite3.connect('tg_gpt_assist.db')


def db_read_thread_id(user_id: int):
    cursor = conn.cursor()
    cursor.execute('SELECT thread_id FROM user_threads WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    return result[0] if result else None


def db_write_thread_id(user_id: int, thread_id: str):
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO user_threads (user_id, thread_id) VALUES (?, ?)
        ON CONFLICT(user_id) DO UPDATE SET thread_id = excluded.thread_id;
    ''', (user_id, thread_id))
    conn.commit()


class TGOpenAI:
    _client = None
    _assist = None

    @classmethod
    def get_client(cls, api_key=None, *args, **kwargs):
        if api_key is None:
            api_key = os.environ["OPENAI_API_KEY"]
        if cls._client is None:
            cls._client = AsyncOpenAI(api_key=api_key)
        return cls._client

    @classmethod
    async def get_assist(cls, assist_id=None, *args, **kwargs):
        if assist_id is None:
            assist_id = os.environ["ASSISTANT_ID"]
        if cls._assist is None:
            cls._assist = await cls._client.beta.assistants.retrieve(assistant_id=assist_id)
        return cls._assist


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        rf"Hi {user.mention_html()}! !"
    )


async def create_thread(client: AsyncOpenAI) -> str:
    """Create a thread."""
    thread = await client.beta.threads.create()
    return thread.id


async def retrieve_thread_id(client: AsyncOpenAI, user_id: int, user_data) -> str:
    """Retrieve a thread."""
    thread_id = user_data.get("thread_id")
    logger.warning(f"thread_id: {thread_id}")
    if not thread_id:
        thread_id = db_read_thread_id(user_id)
        logger.warning(f"db_thread_id: {thread_id}")
        if not thread_id:
            thread_id = await create_thread(client)
            db_write_thread_id(user_id, thread_id)
        user_data["thread_id"] = thread_id
    return thread_id


async def ask_question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Echo the user message."""
    query = update.message.text
    user_id = update.effective_user.id
    user_data = context.user_data
    thread_id = await retrieve_thread_id(TGOpenAI.get_client(), user_id, user_data)

    await update.message.reply_text(f"Your thread_id is {thread_id}")


async def async_setup():
    """Asynchronous setup for the bot."""
    client = AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"])
    assist_id = os.environ.get("ASSISTANT_ID")
    assistant = await async_retrieve_assistant(client, assist_id)
    return assistant


def main() -> None:
    bot_token = os.environ.get("TG_TOKEN")
    application = Application.builder().token(bot_token).build()

    application.add_handler(CommandHandler("start", start))

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ask_question))

    application.run_polling(allowed_updates=Update.ALL_TYPES)


def init_db():
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_threads (
            user_id INT PRIMARY KEY,
            thread_id TEXT
        )
    ''')
    conn.commit()


if __name__ == "__main__":
    init_db()
    main()
