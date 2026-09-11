import uuid
import spaces
from typing import List, Tuple
from chatbot.load_config import LoadProjectConfig
from agent_graph.load_tools_config import LoadToolsConfig
from agent_graph.build_full_graph import build_graph
from utils.app_utils import create_directory

URL = "https://github.com/Farzad-R/LLM-Zero-to-Hundred/tree/master/RAG-GPT"
hyperlink = f"[RAG-GPT user guideline]({URL})"

PROJECT_CFG = LoadProjectConfig()
TOOLS_CFG = LoadToolsConfig()

graph = build_graph()


class ChatBot:
    """
    A class to handle chatbot interactions by utilizing a pre-defined agent graph. The chatbot processes
    user messages, generates appropriate responses, and passes them to the UI.
    """
    
    @staticmethod
    def load_history(session_id: str) -> Tuple[str, List]:
        """
        Called on page load. Initializes a session ID if empty, and fetches historical
        messages from LangGraph MemorySaver for that session ID to populate the UI.
        """
        if not session_id:
            session_id = str(uuid.uuid4())
            return session_id, []
            
        config = {"configurable": {"thread_id": session_id}}
        try:
            state = graph.get_state(config)
            if state and "messages" in state.values:
                messages = state.values["messages"]
                chatbot_history = []
                for msg in messages:
                    if msg.type == "human":
                        chatbot_history.append({"role": "user", "content": msg.content})
                    elif msg.type == "ai" and msg.content:
                        chatbot_history.append({"role": "assistant", "content": msg.content})
                return session_id, chatbot_history
        except Exception as e:
            print(f"Error loading history: {e}")
            
        return session_id, []

    @staticmethod
    @spaces.GPU
    def respond(chatbot: List, message: str, session_id: str) -> Tuple:
        """
        Processes a user message using the agent graph, generates a response, and appends it to the chat history.
        """
        if not session_id:
            session_id = str(uuid.uuid4())
            
        config = {"configurable": {"thread_id": session_id}}
        
        events = graph.stream(
            {"messages": [("user", message)]}, config, stream_mode="values"
        )
        for event in events:
            event["messages"][-1].pretty_print()

        chatbot.append({"role": "user", "content": message})
        chatbot.append({"role": "assistant", "content": event["messages"][-1].content})

        return "", chatbot
