from bs4 import BeautifulSoup
from langchain_community.document_loaders.recursive_url_loader import RecursiveUrlLoader
from langchain_core.prompts import PromptTemplate
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.tools import tool
from src.apis.controllers.location_controller import get_weather_api
from src.langgraph.langchain.llm import llm_flash
from src.utils.logger import logger
from langchain_community.tools import DuckDuckGoSearchResults

search_tavily = TavilySearchResults(max_results=2)
search_duck = DuckDuckGoSearchResults(output_format="list", max_results=5)


# @tool
# async def search_and_summarize_website(query: str):
#     """A search engine optimized for comprehensive, accurate, and trusted results.
#         Useful for when you need to answer questions about current events.
#         Input should be a search query."
#     Args:
#         query (str): The search query for search engine. Using Vietnamese language for better results.
#     """

#     results = search_duck.invoke(query)
#     content = "\n".join(
#         [
#             f"Snippet {int(index)+1}: {r.get('snippet')}"
#             for index, r in enumerate(results)
#         ]
#     )

#     # Define prompt
#     prompt = PromptTemplate.from_template(
#         "Write a concise summary of the following:\\n\\n{context}"
#     )

#     chain = prompt | llm_flash
#     results = await chain.ainvoke({"context": content})

#     return results.content


@tool
async def search_and_summarize_website(query: str):
    """A search engine optimized for comprehensive, accurate, and trusted results.
        Useful for when you need to answer questions about current events.
        Input should be a search query."
    Args:
        query (str): The search query for search engine. Using Vietnamese language for better results.
    """
    results = await search_tavily.ainvoke(query)
    logger.info(f"-> Search results: {results}")
    content = "\n==========\n".join([result["content"] for result in results])
    return content
