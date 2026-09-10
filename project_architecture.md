# Project Architecture & Flow

This document outlines the exact tools, agents, classes, and functions used across the project to help you understand how everything connects together. 

The project is built on **LangGraph** (an extension of LangChain), which treats the AI workflow as a State Graph where the AI ("Agent") cycles between thinking, calling tools, and returning answers to the user.

---

## 1. The Core Agent & Graph Engine
*(Located in `src/agent_graph/`)*

These components build the actual "brain" of the AI, defining how it thinks and decides when to use tools.

* **`def build_graph()`** *(in `build_full_graph.py`)*
  * The main engine function. It initializes the Gemini LLM model, binds all the tools to it, and constructs the LangGraph state machine. It connects the "chatbot" node to the "tools" node.
* **`class State(TypedDict)`** *(in `agent_backend.py`)*
  * Defines the memory structure passed between nodes in the graph (i.e., the list of messages).
* **`class BasicToolNode`** *(in `agent_backend.py`)*
  * A custom node that catches tool requests from the AI, executes the actual python tool function (like querying SQL), and passes the raw result back to the AI.
* **`def route_tools()`** *(in `agent_backend.py`)*
  * The conditional router. It checks the AI's last output. If the AI requested a tool, it routes to `BasicToolNode`. If not, it routes to "END" and displays the answer to the user.

---

## 2. The Tools
*(Located in `src/agent_graph/`)*

These are the specialized functions the AI is allowed to call when it doesn't know the answer off the top of its head.

#### Web Search
* **`def load_tavily_search_tool()`** *(in `tool_tavily_search.py`)*
  * Instantiates the Tavily API tool, allowing the AI to search the live internet for recent news.

#### Vector Database (RAG) Tools
* **`class StoriesRAGTool`** & **`def lookup_stories()`** *(in `tool_stories_rag.py`)*
  * Connects to the Chroma DB. The AI calls `lookup_stories(query)` to search for paragraphs about fictional stories.
* **`class SwissAirlinePolicyRAGTool`** & **`def lookup_swiss_airline_policy()`** *(in `tool_lookup_policy_rag.py`)*
  * Connects to the Chroma DB. The AI calls `lookup_swiss_airline_policy(query)` to find rules regarding airline baggage, pets, cancellations, etc.

#### Relational Database (SQL) Tools
* **`class TravelSQLAgentTool`** & **`def query_travel_sqldb()`** *(in `tool_travel_sqlagent.py`)*
  * Uses LangChain's SQLDatabase toolkit. The AI calls `query_travel_sqldb()` to write raw SQL queries against the 100MB Travel database to find flights and bookings.
* **`class ChinookSQLAgent`** & **`def query_chinook_sqldb()`** *(in `tool_chinook_sqlagent.py`)*
  * Uses LangChain's SQL toolkit. The AI calls `query_chinook_sqldb()` to query the digital music store database.
  * *Helper classes*: `class Table`, `class TableList`, and `def get_tables()` are used specifically in this script to help dynamically filter which SQL tables the AI is allowed to see.

---

## 3. The Chatbot Backend (Gradio Server)
*(Located in `src/chatbot/`)*

These classes handle the actual User Interface and user inputs.

* **`class ChatBot`** *(in `chatbot_backend.py`)*
  * The primary class instantiated by `app.py`. It takes your text from the Gradio text box, passes it into the LangGraph `build_graph()` instance, yields the streaming output, and handles the chat history formatting.
* **`class Memory`** *(in `memory.py`)*
  * Responsible for saving the chat history. (For example, it converts the Gradio dictionary message format into persistent storage so the AI remembers what you said previously).
* **`class LoadProjectConfig`** *(in `load_config.py`)*
  * Loads the system prompts (the instructions telling Gemini how to behave) and general UI settings.

---

## 4. Configuration & Utilities
*(Located in `src/utils/` and the project root)*

These are background helper scripts that set up the environment.

* **`class LoadToolsConfig`** *(in `load_tools_config.py`)*
  * Parses your `configs/tools_config.yml` file (where we just updated the `k` parameter to 6) to load chunk sizes, chunk limits, and embedding model names.
* **`class PrepareVectorDB`** *(in `prepare_vector_db.py`)*
  * The background script we recently updated with the incremental check logic. You run this manually to convert PDFs into Chroma Vector Databases.
* **`class UISettings`** *(in `utils/ui_settings.py`)*
  * Defines specific CSS or layout settings for the Gradio web interface.
* **`def create_directory()`** *(in `utils/app_utils.py`)*
  * A tiny helper function to ensure output folders exist before trying to write to them.
