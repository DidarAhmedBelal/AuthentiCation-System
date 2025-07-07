import requests
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from .models import Message

# Setup your LLM client
llm = ChatOllama(model="llama3.2:3b", base_url="http://localhost:11434")
output_parser = StrOutputParser()

def generate_response_from_chat(chat, user, user_input):
    """
    Generate a dynamic AI response using LangChain Ollama.
    You can pass in chat context (messages) if you want.
    """

    # Fetch last messages of this chat for context, ordered oldest->newest
    recent_messages = Message.objects.filter(chat=chat).order_by('timestamp')[:10]

    # Build messages list in LangChain format (role, content)
    messages = [("system", "You are a helpful assistant specialized in sports coaching.")]

    for msg in recent_messages:
        role = "assistant" if msg.sender.username == "chatbot" else "user"
        messages.append((role, msg.content))

    # Append current user input as last user message
    messages.append(("user", user_input))

    # Build prompt and invoke LLM chain
    prompt = ChatPromptTemplate.from_messages(messages)
    chain = prompt | llm | output_parser

    # Get the response string
    response = chain.invoke({})

    return response, messages  # you can return chat log or whatever you want
