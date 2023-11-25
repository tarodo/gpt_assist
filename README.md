# DataPilot Aide

## 🔍 Overview
**DataPilot Aide** is a dynamic partner for data engineers, analysts, and data scientists; and it's more than just a bot. Powered by OpenAI's GPT models, it offers an intuitive and intelligent helping hand, transforming complex data queries into clear insights. This bot is a fusion of Telegram's seamless interface and cutting-edge AI, making it a go-to resource for quick, accurate, and context-aware assistance. Whether it's guiding through intricate data challenges or offering analysis support, DataPilot Aide is designed to energize and streamline the workflow of data professionals, bringing a touch of AI brilliance to every interaction.
## ✨ Features
- 🛠️ **Professional Role Integration**: Recognizes the user as a data engineer with specializations in various data engineering tools.
- 🤝 **Project and Challenge Collaboration**: Offers strategies for efficient data flow and processing.
- 🚀 **Interest in Data Engineering Technologies**: Keeps the user updated on the latest trends in data engineering.
- 📚 **Learning Style Adaptation**: Uses practical examples and workflow diagrams for explaining concepts.
- 💡 **Analytical Problem-Solving**: Integrates data engineering logic with analytical reasoning for well-rounded solutions.

## 💻 Tech Features
| Feature                          | Description |
|----------------------------------|-------------|
| **AI-Powered Conversations**     | Engage in seamless and intelligent dialogues with the AI assistant, powered by OpenAI's GPT models. |
| **Persistent Context Management**| The bot maintains conversation context, ensuring continuity and relevance in interactions. |
| **Dynamic Response Generation**  | Generates responses based on user queries, offering informative and contextually appropriate answers. |
| **User-Specific Thread Management** | Manages individual threads for each user, ensuring personalized and uninterrupted conversations. |
| **Real-Time Interaction**        | Designed to respond promptly, providing a smooth and engaging user experience. |
| **Error Handling**               | Gracefully manages unexpected situations or errors, ensuring the bot remains operational and user-friendly. |

## 🛠️ Behind the Scenes
- **Database Integration**: Utilizes [SQLite](https://www.sqlite.org/index.html) for managing user-specific data, ensuring efficient and secure data handling.
- **Asynchronous Operations**: Leverages Python's [asyncio](https://docs.python.org/3/library/asyncio.html) for non-blocking operations, enhancing performance and scalability.
- **Robust Error Handling**: Implements [error handling mechanisms](https://vegibit.com/python-error-handling-best-practices/) to manage and respond to various exceptions gracefully.
- **Markdown Support**: Supports [Markdown V2](https://core.telegram.org/bots/api#markdownv2-style) for formatting messages, making the responses more readable and engaging.
- **Environment Variable Management**: Uses environment variables for configuration, ensuring security and flexibility through tools like [dotenv](https://pypi.org/project/python-dotenv/).

## 📋 Requirements
- [Docker Compose](https://docs.docker.com/compose/install/)

## 📥 Installation
1. Clone the repository or download the script.
2. Set up your `.env` file with:
   - `OPENAI_API_KEY`: (required) [OpenAI API key](https://platform.openai.com/api-keys)
   - `TAVILY_API_KEY`: (required) [Tavily API key](https://app.tavily.com/home)
   - `OPENAI_MODEL`: [OpenAI model ID](https://platform.openai.com/docs/models/overview)
   - `ASSISTANT_ID`: (required) [GPT Assistant](https://platform.openai.com/assistants)
   - `TELEGRAM_TOKEN`: (required) [Telegram bot token](https://t.me/BotFather)

## 👩‍💻 Usage
1. Run the script: 
   ```shell
   docker-compose up -d
   ```