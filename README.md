# Data Engineering Assistant Script

## Overview
This script is designed to serve as an assistant for data engineers, focusing on building, maintaining, and optimizing data pipelines and architectures. It specializes in tools like PySpark, Airflow, MinIO, Impala, Greenplum, and DataIKU, requiring expertise in data processing, storage, and workflow orchestration. The script utilizes OpenAI and Tavily APIs to provide comprehensive assistance.

## Features
- **Professional Role Integration**: Recognizes the user as a data engineer with specializations in various data engineering tools.
- **Project and Challenge Collaboration**: Offers strategies for efficient data flow and processing.
- **Interest in Data Engineering Technologies**: Keeps the user updated on the latest trends in data engineering.
- **Learning Style Adaptation**: Uses practical examples and workflow diagrams for explaining concepts.
- **Analytical Problem-Solving**: Integrates data engineering logic with analytical reasoning for well-rounded solutions.

## Requirements
- Python 3.11
- `openai` Python package
- `tavily` Python package
- `python-dotenv` package for environment variable management

## Installation
1. Clone the repository or download the script.
2. Start a virtual environment: `python -m venv venv`
3. Install required Python packages: `pip install -r requirements.txt`
4. Set up your `.env` file with:
   - `OPENAI_API_KEY`: (required) [OpenAI API key](https://platform.openai.com/api-keys)
   - `TAVILY_API_KEY`: (required) [Tavily API key](https://app.tavily.com/home)
   - `OPENAI_MODEL`: [OpenAI model ID](https://platform.openai.com/docs/models/overview)

## Usage
1. Run the script: `python main.py`
2. Interact with the assistant through the command line interface.
3. Type `exit` to end the session.