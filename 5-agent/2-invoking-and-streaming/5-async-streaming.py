import os
import asyncio


from dotenv import load_dotenv, find_dotenv   # from the python-dotenv library - load the OpenAI API key from file
from langchain_openai import ChatOpenAI


load_dotenv(override=True)     # This will load the OpenAI API key from the .env file
# Grab the key manually to ensure it's actually there
my_key = os.getenv("OPENAI_API_KEY")
print(my_key)

# --- SYNCHRONOUS SETUP ---
# Standard instantiation (langchain-openai >= 0.1.0)
model = ChatOpenAI(model="gpt-4o",
                   api_key=my_key)

async def stream_directly(user_text):
    print("AI Response: ", end="", flush=True)
    
    # --- THE PRINT LOOP ---
    # We pass the string directly to astream
    # No prompt templates, no pipes, no middle-men
    async for chunk in model.astream(user_text):
        print(chunk.content, end="|", flush=True)

if __name__ == "__main__":
    user_query = "Write 50 lines of text about butterflies."
    asyncio.run(stream_directly(user_query))