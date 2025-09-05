from langchain_groq import ChatGroq
from langchain.schema import AIMessage, HumanMessage
from langchain.prompts import PromptTemplate
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

GROQ_API_KEY = os.getenv("groq_api_key")

# Default model
DEFAULT_MODEL = "llama-3.3-70b-versatile"

# Dictionary to store model-specific chatbots
model_chatbots = {}

def get_chatbot(model_name=DEFAULT_MODEL):
    """Get or create a chatbot instance for the specified model"""
    # Try to use the requested model, fall back to default if there's an issue
    try:
        if model_name not in model_chatbots:
            model_chatbots[model_name] = ChatGroq(model_name=model_name, api_key=GROQ_API_KEY)
        return model_chatbots[model_name]
    except Exception as e:
        print(f"Error initializing model {model_name}: {e}")
        # If the requested model is already the default, try llama-3.1-8b-instant as ultimate fallback
        if model_name == DEFAULT_MODEL:
            fallback_model = "llama-3.1-8b-instant"
            print(f"Default model failed, trying fallback model: {fallback_model}")
            if fallback_model not in model_chatbots:
                model_chatbots[fallback_model] = ChatGroq(model_name=fallback_model, api_key=GROQ_API_KEY)
            return model_chatbots[fallback_model]
        # Otherwise fall back to the default model
        print(f"Falling back to default model: {DEFAULT_MODEL}")
        if DEFAULT_MODEL not in model_chatbots:
            model_chatbots[DEFAULT_MODEL] = ChatGroq(model_name=DEFAULT_MODEL, api_key=GROQ_API_KEY)
        return model_chatbots[DEFAULT_MODEL]

# Initialize default chatbot
chatbot = get_chatbot(DEFAULT_MODEL)

prompt_template = PromptTemplate(
    input_variables=["chat_history", "user_input"],
    template="You are a helpful movie recommendation assistant. Here is the conversation so far:\n{chat_history}\nUser: {user_input}\nAssistant:"
)

conversation_chain = prompt_template | chatbot

def clean_json_response(content):
    """Clean JSON content from markdown code blocks and other formatting"""
    # Check for ``` tags and extract any JSON found within
    if "```" in content and "```" in content:
        # Try to find JSON within the think tags
        think_content = content.split("```")[-1].strip()
        if think_content.startswith("```json") or think_content.startswith("```"):
            content = think_content
        elif "{" in think_content and "}" in think_content:
            # Extract just the JSON part
            json_start = think_content.find("{")
            json_end = think_content.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                content = think_content[json_start:json_end]
    
    # Remove markdown code block syntax if present
    if content.startswith("```") and content.endswith("```"):
        # Remove the first and last line (code block markers)
        content = "\n".join(content.split("\n")[1:-1])
    elif content.startswith("```json") and content.endswith("```"):
        content = "\n".join(content.split("\n")[1:-1])
    
    # For cases where just the pattern ```json or ``` is present without proper formatting
    content = content.strip().replace("```json", "").replace("```", "").strip()
    
    return content