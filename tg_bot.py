import asyncio
import json
import logging
import os
import sqlite3

from openai import AsyncOpenAI, BadRequestError
from openai.types.beta.threads import RequiredActionFunctionToolCall
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from dotenv import load_dotenv

from gpt import tavily_search, TAVILY_CLIENT, get_last_message

load_dotenv()

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
    _client: AsyncOpenAI = None
    assist_id: str = os.environ["ASSISTANT_ID"]

    @classmethod
    def get_client(cls, api_key=None, *args, **kwargs):
        if api_key is None:
            api_key = os.environ["OPENAI_API_KEY"]
        if cls._client is None:
            cls._client = AsyncOpenAI(api_key=api_key)
        return cls._client


async def create_thread(client: AsyncOpenAI) -> str:
    """Create a thread."""
    thread = await client.beta.threads.create()
    return thread.id


async def retrieve_thread_id(client: AsyncOpenAI, user_id: int, user_data) -> str:
    """Retrieve a thread."""
    thread_id = user_data.get("thread_id")
    if not thread_id:
        thread_id = db_read_thread_id(user_id)
        if not thread_id:
            thread_id = await create_thread(client)
            db_write_thread_id(user_id, thread_id)
        user_data["thread_id"] = thread_id
    return thread_id


async def renew_thread(client: AsyncOpenAI, user_id: int, user_data):
    new_thread_id = await create_thread(client)
    db_write_thread_id(user_id, new_thread_id)
    user_data["thread_id"] = new_thread_id


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await renew_thread(TGOpenAI.get_client(), user.id, context.user_data)
    await update.message.reply_html(
        rf"Hi {user.mention_html()}! !"
    )


def create_tool_outputs(tools_to_call: list[RequiredActionFunctionToolCall]):
    tool_output_array = []
    for tool in tools_to_call:
        output = None
        tool_call_id = tool.id
        function_name = tool.function.name
        function_args = tool.function.arguments

        if function_name == "tavily_search":
            output = tavily_search(TAVILY_CLIENT, query=json.loads(function_args)["query"])

        if output:
            tool_output_array.append({"tool_call_id": tool_call_id, "output": output})
    return tool_output_array


def escape_characters(text: str) -> str:
    """Screen characters for Markdown V2"""
    text = text.replace('\\', '')
    text = text.replace('**', '*')

    characters = ['.', '+', '(', ')', '-', '_', "!", ">", "<"]
    for character in characters:
        text = text.replace(character, f'\{character}')
    return text


async def send_status(status_message, status: str, status_cnt: int = 0, desc: str = None):
    answers = {
        "start": "Starting run",
        "in_progress": "In progress",
        "requires_action": "Searching in Internet",
        "completed": "Completed",
        "error": "Error",
    }
    msg = f">>> *Status* :: {answers.get(status, 'Waiting')}{'.' * status_cnt}{f' :: {desc}' if desc else ''}"
    msg = escape_characters(msg)
    if status_cnt == -1:
        status_message = await status_message.reply_markdown_v2(msg)
    else:
        await status_message.edit_text(msg, parse_mode=ParseMode.MARKDOWN_V2)
    return status_message


async def async_wait_for_run_completion(client: AsyncOpenAI, thread_id: str, run_id: str, status_message):
    cur_status = "in_progress"
    status_cnt = 0
    while True:
        await asyncio.sleep(1)
        run = await client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)
        await send_status(status_message, run.status, status_cnt)
        if run.status == cur_status:
            status_cnt += 1
        else:
            cur_status = run.status
            status_cnt = 0
        if run.status in ['completed', 'failed', 'requires_action']:
            return run


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = ("Sorry, I have some problems to answer your question. "
           "Please try again later or start new chat with /start command.")
    await update.message.reply_text(msg)


async def ask_question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Echo the user message."""
    query = update.message.text
    client = TGOpenAI.get_client()
    assist_id = TGOpenAI.assist_id
    user_id = update.effective_user.id
    user_data = context.user_data
    thread_id = await retrieve_thread_id(client, user_id, user_data)
    try:
        await client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=query,
        )
    except BadRequestError as e:
        logger.error(e)
        await error_handler(update, context)
        return

    run = await client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=assist_id,
    )

    status_message = await send_status(update.message, "start", -1)

    run = await async_wait_for_run_completion(client, thread_id, run.id, status_message)
    if run.status == 'failed':
        await send_status(status_message, "error", desc=run.last_error.message)
    elif run.status == 'requires_action':
        actions = run.required_action.submit_tool_outputs.tool_calls
        tool_output = create_tool_outputs(actions)
        run = await client.beta.threads.runs.submit_tool_outputs(
            thread_id=thread_id,
            run_id=run.id,
            tool_outputs=tool_output
        )
        await async_wait_for_run_completion(client, thread_id, run.id, status_message)

    msg = await get_last_message(client, thread_id)
    msg = msg.content[0].text.value
    msg = escape_characters(msg)
    await status_message.edit_text(f"{msg}", parse_mode=ParseMode.MARKDOWN_V2)


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
