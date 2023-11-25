import asyncio
import os
import json
import time
from openai import OpenAI, AsyncOpenAI
from openai.pagination import AsyncCursorPage
from openai.types.beta.threads import RequiredActionFunctionToolCall
from tavily import TavilyClient
from dotenv import load_dotenv

from assistant_conf import assistant_description, assistant_prompt_instruction

load_dotenv()
OPENAI_CLIENT = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-3.5-turbo-1106")
TAVILY_CLIENT = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])


def retrieve_assistant(client: OpenAI, assistant_id: str):
    return client.beta.assistants.retrieve(assistant_id=assistant_id)


async def async_retrieve_assistant(client: AsyncOpenAI, assistant_id: str):
    return await client.beta.assistants.retrieve(assistant_id=assistant_id)


def create_assistant(client: OpenAI, description: str, prompt_instruction: str):
    assistant = client.beta.assistants.create(
        instructions=prompt_instruction,
        description=description,
        model=OPENAI_MODEL,
        tools=[{
            "type": "function",
            "function": {
                "name": "tavily_search",
                "description": "Get information on recent events from the web.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string",
                                  "description": "The search query to use. "
                                                 "For example: 'Latest news of pySpark'"},
                    },
                    "required": ["query"]
                }
            }
        }, {"type": "code_interpreter"}]
    )
    print(f"Assistant ID: {assistant.id}")
    return assistant


def create_thread(client: OpenAI):
    thread = client.beta.threads.create()
    print(f"Thread: {thread}")
    return thread


def tavily_search(tavily_client: TavilyClient, query: str):
    search_result = tavily_client.get_search_context(query, search_depth="advanced", max_tokens=8000)
    return search_result


def wait_for_run_completion(thread_id: str, run_id: str):
    while True:
        time.sleep(1)
        run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)
        print(f"Current run status: {run.status}")
        if run.status in ['completed', 'failed', 'requires_action']:
            return run


def submit_tool_outputs(thread_id: str, run_id: str, tools_to_call: list[RequiredActionFunctionToolCall]):
    tool_output_array = []
    for tool in tools_to_call:
        output = None
        tool_call_id = tool.id
        function_name = tool.function.name
        function_args = tool.function.arguments

        if function_name == "tavily_search":
            output = tavily_search(query=json.loads(function_args)["query"])

        if output:
            tool_output_array.append({"tool_call_id": tool_call_id, "output": output})

    return client.beta.threads.runs.submit_tool_outputs(
        thread_id=thread_id,
        run_id=run_id,
        tool_outputs=tool_output_array
    )


def print_messages_from_thread(thread_id):
    messages = client.beta.threads.messages.list(thread_id=thread_id)
    for msg in messages:
        print(f"{msg.role}: {msg.content[0].text.value}")


async def get_last_message(client, thread_id):
    messages: AsyncCursorPage = await client.beta.threads.messages.list(thread_id=thread_id, order="desc")
    return messages.data[0]


if __name__ == '__main__':
    client = OPENAI_CLIENT
    assistant = create_assistant(client, assistant_description, assistant_prompt_instruction)
    thread = create_thread(client)
    while True:
        user_input = input("You: ")
        if user_input.lower() == 'exit':
            break

        # Create a message
        message = client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=user_input,
        )

        # Create a run
        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=assistant.id,
        )
        print(f"Run ID: {run.id}")

        # Wait for run to complete
        run = wait_for_run_completion(thread.id, run.id)

        if run.status == 'failed':
            print(run.error)
            continue
        elif run.status == 'requires_action':
            actions = run.required_action.submit_tool_outputs.tool_calls
            run = submit_tool_outputs(thread.id, run.id, actions)
            run = wait_for_run_completion(thread.id, run.id)

        # Print messages from the thread
        print_messages_from_thread(thread.id)
