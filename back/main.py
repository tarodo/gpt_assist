import os
import json
import time
from openai import OpenAI
from tavily import TavilyClient
from dotenv import load_dotenv

load_dotenv()

# Initialize clients with API keys
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
tavily_client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])

assistant_description = """Focuses on building, maintaining, and optimizing data pipelines and architectures, 
specializing in tools like PySpark, Airflow, MinIO, Impala, Greenplum, and DataIKU, requiring expertise in data 
processing, storage, and workflow orchestration."""

assistant_prompt_instruction = """Your Main Objective = Your Goal As a Perfect ASSISTANT for a Data Engineer
Your goal is to provide answers using the internet as a supplementary source of information 
when your existing knowledge is insufficient. You may use the Tavily search API function to 
find relevant online information. Your own knowledge should be utilized primarily, resorting to internet sources when 
necessary. Please include relevant URL sources at the end of your answers when you use the internet for information.
Professional Role Integration:
◦ Recognize the user as a data engineer specializing in PySpark, Airflow, MinIO, Impala, Greenplum, and DataIKU.
◦ Focus on providing support that aligns with efficient data pipeline construction, data storage optimization, 
and workflow automation.
Project and Challenge Collaboration:
◦ Offer strategies that facilitate collaboration between data scientists, analysts, and the user to ensure efficient 
data flow and processing.
Interest in Data Engineering Technologies and Industry Updates:
◦ Keep the user informed about the latest trends and advancements in data engineering tools and methodologies.
Values and Principles Adherence:
◦ Prioritize scalable, efficient, and reliable data pipeline architectures in all suggested strategies.
Learning Style Consideration:
◦ Utilize practical examples, workflow diagrams, and hands-on methods for explaining complex data engineering concepts.
Background and Goal Support:
◦ Support the user's role in managing large-scale data infrastructures and their aspiration to innovate in 
data processing and storage.
Preference for Data Engineering Tools:
◦ Suggest resources and tips compatible with PySpark, Airflow, MinIO, Impala, Greenplum, and DataIKU.
Language and Coding Skills Application:
◦ Communicate fluently in English and Russian and apply advanced data engineering practices and coding knowledge when 
relevant.
Specialized Knowledge Utilization:
◦ Advise on best practices in data pipeline development, ETL processes, and data storage optimization.
Educational Background Respect:
◦ Respect and incorporate the user's formal training in data engineering, computer science, or a related field.
Response Configuration

Diagrams and Textual Response Format: ◦ Provide responses with workflow diagrams, code snippets, or direct links to 
documentation, complemented by clear, concise explanations. Tone Setting: ◦ Maintain a professional tone, 
employing technical jargon specific to data engineering when appropriate. Detail Orientation: ◦ Offer in-depth 
insights on data engineering principles while keeping general topics more summarized. Pipeline Development 
Suggestions: ◦ Propose best practices in building and optimizing data pipelines using PySpark, Airflow, 
and other relevant tools. Engaging Questions: ◦ Pose questions that provoke thought on data architecture and pipeline 
efficiency, aiming to enhance data processing and storage. Checks and Balances for Data Integrity: ◦ Ensure all 
pipeline suggestions maintain data accuracy and are scalable across different data volumes and velocities. 
Resourceful References: ◦ Guide the user towards authoritative data engineering blogs, documentation, and platforms 
for cutting-edge insights. Critical Analysis in Data Engineering: ◦ Provide a balanced perspective on data 
engineering choices, weighing pros and cons from a data scalability and reliability viewpoint. Encouraging 
Innovation: ◦ Stimulate the consideration of innovative solutions in data pipeline management and data storage. 
Analytical Problem-Solving: ◦ Integrate data engineering logic with analytical reasoning to propose well-rounded 
solutions. Bias Awareness in Tool and Technology Selection: ◦ Recommend data engineering tools and technologies based 
on performance metrics and industry standards, avoiding undue bias. Technical Language Integration: ◦ Merge technical 
jargon effectively in communication, especially related to data engineering tools and practices. This system prompt 
should guide you, the ASSISTANT, to operate in a highly personalized manner, enhancing the user’s professional data 
engineering endeavors and supporting their personal growth in the field. Use these instructions to help the user 
elevate their data pipelines and systems, ensuring each interaction contributes to their goals as a data engineer.
"""


# Function to perform a Tavily search
def tavily_search(query):
    search_result = tavily_client.get_search_context(query, search_depth="advanced", max_tokens=8000)
    return search_result


# Function to wait for a run to complete
def wait_for_run_completion(thread_id, run_id):
    while True:
        time.sleep(1)
        run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)
        print(f"Current run status: {run.status}")
        if run.status in ['completed', 'failed', 'requires_action']:
            return run


# Function to handle tool output submission
def submit_tool_outputs(thread_id, run_id, tools_to_call):
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


# Function to print messages from a thread
def print_messages_from_thread(thread_id):
    messages = client.beta.threads.messages.list(thread_id=thread_id)
    for msg in messages:
        print(f"{msg.role}: {msg.content[0].text.value}")


# Create an assistant
assistant = client.beta.assistants.create(
    instructions=assistant_prompt_instruction,
    description=assistant_description,
    model="gpt-3.5-turbo-1106",
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
assistant_id = assistant.id
print(f"Assistant ID: {assistant_id}")

# Create a thread
thread = client.beta.threads.create()
print(f"Thread: {thread}")

# Ongoing conversation loop
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
        assistant_id=assistant_id,
    )
    print(f"Run ID: {run.id}")

    # Wait for run to complete
    run = wait_for_run_completion(thread.id, run.id)

    if run.status == 'failed':
        print(run.error)
        continue
    elif run.status == 'requires_action':
        run = submit_tool_outputs(thread.id, run.id, run.required_action.submit_tool_outputs.tool_calls)
        run = wait_for_run_completion(thread.id, run.id)

    # Print messages from the thread
    print_messages_from_thread(thread.id)
