from langchain_google_genai import ChatGoogleGenerativeAI

# llm = ChatGoogleGenerativeAI(
#     model="gemini-1.5-flash",
#     temperature=0.1,
#     max_retries=2,
# )
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    temperature=0.1,
    # max_retries=2,
)
llm_flash = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    temperature=0.1,
    # max_retries=2,
)
