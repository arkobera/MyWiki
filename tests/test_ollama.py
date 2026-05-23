from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage

# Initialize local Ollama model
llm = ChatOllama(
    model="phi3:mini",
    temperature=0.7
)

# Simple test prompt
response = llm.invoke(
    [
        HumanMessage(
            content="Explain transformers in simple terms."
        )
    ]
)

print("\n===== MODEL RESPONSE =====\n")
print(response.content)