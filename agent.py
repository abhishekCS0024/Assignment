import os
import json
import time
import requests
from typing import TypedDict, Annotated, List, Dict, Optional
from pydantic import BaseModel, Field
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_groq import ChatGroq
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_community.tools.wikipedia.tool import WikipediaQueryRun
from langchain_community.utilities.wikipedia import WikipediaAPIWrapper


from Rag_Pipeline.neo4j_retreival import  retriever

# llm = ChatGroq(
#         temperature=0.7,
#         groq_api_key=os.getenv("GROQ_API_KEY"),
#         model_name="qwen/qwen3-32b"
#     )

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise RuntimeError(
        "GROQ_API_KEY is not set. "
        "Run: setx GROQ_API_KEY \"your_key\" and restart terminal."
    )

llm = ChatGroq(
    temperature=0.7,
    groq_api_key=GROQ_API_KEY,
    model_name="qwen/qwen3-32b"
)

class LinkedInGrowthState(TypedDict):
    desc: str
    expertise: str
    target_audience: str
    
    niche: str
    content_theme: str
    tone: str

    retrieved_posts: List[Dict]
    patterns: List[Dict]

    generated_posts: List[Dict]
    niche_summary: str
    content_strategy: str

    messages: Annotated[List[BaseMessage], add_messages]

class NicheEvaluation(BaseModel):
    niche: str
    content_theme: str
    tone: str

def agent_a_auditor(state: LinkedInGrowthState):
    evaluator = llm.with_structured_output(NicheEvaluation)

    messages = [
        SystemMessage(
            content="Analyze the user and identify niche, content themes, and tone."
        ),
        HumanMessage(
            content=f"""
                DESCRIPTION: {state['desc']}
                EXPERTISE: {state['expertise']}
                TARGET AUDIENCE: {state['target_audience']}
            """
        ),
    ]

    result = evaluator.invoke(messages)

    return {
        "niche": result.niche,
        "content_theme": result.content_theme,
        "tone": result.tone
    }

class PatternExtraction(BaseModel):
    hook: str
    structure: str
    cta: str
    keywords: List[str]

def agent_b_analyst(state: LinkedInGrowthState):
    query = f"successful high engagement {state['niche']} posts"
    results = retriever(query)

    retrieved_posts = [
        {"text": doc.page_content, "metadata": doc.metadata}
        for doc in results[:5]
    ]

    posts_text = "\n---\n".join(p["text"][:500] for p in retrieved_posts)
    
    extractor = llm.with_structured_output(PatternExtraction)

    messages = [
        SystemMessage(content="Extract content patterns from text."),
        HumanMessage(content=posts_text)
    ]

    out = extractor.invoke(messages)

    patterns = [{
        "hook": out.hook,
        "structure": out.structure,
        "cta": out.cta,
        "keywords": out.keywords
    }]

    return {
        "retrieved_posts": retrieved_posts,
        "patterns": patterns
    }

class LinkedInPost(BaseModel):
    day: int
    posting_day: str
    content_type: str
    hook: str
    post_text: str
    hashtags: List[str]
    cta: str
    image_query: str = Field(description="Search query for finding relevant images")

class ContentPlan(BaseModel):
    niche_summary: str
    content_strategy: str
    posts: List[LinkedInPost]

duck_search = DuckDuckGoSearchRun()
wiki_search = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())

def search_images_pexels(query: str, max_results: int = 3) -> List[Dict[str, str]]:
    """
    Pexels API - Free tier: 200 requests/hour
    Get API key: https://www.pexels.com/api/
    """
    
    try:
        headers = {"Authorization": os.getenv("PIXEL")}
        url = f"https://api.pexels.com/v1/search?query={query}&per_page={max_results}"
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            images = []
            for photo in data.get('photos', []):
                images.append({
                    "url": photo['src']['large'],
                    "photographer": photo['photographer'],
                    "source": "Pexels",
                    "description": query
                })
            return images
        else:
            print(f"⚠️ Pexels API error: {response.status_code}")
            return []
    except Exception as e:
        print(f"⚠️ Pexels error: {e}")
        return []

def agent_c_creator(state: LinkedInGrowthState):
    
    creator = llm.with_structured_output(ContentPlan)

    niche = state["niche"]

    search_query = f"latest trends in {niche}"
    duck = duck_search.run(search_query)

    wiki_query = niche
    wiki = wiki_search.run(wiki_query)

    patterns_text = ""
    for p in state["patterns"]:
        patterns_text += f"Hook: {p['hook']}\nStructure: {p['structure']}\nCTA: {p['cta']}\nKeywords: {p['keywords']}\n"

    messages = [
        SystemMessage(content="""
        
        You are a senior LinkedIn ghost-writer who specialises in long-form thought-leadership carousels and posts.
        Generate a 5-day LinkedIn content plan each post must be be of 280 to 350 words in a well structure format. For each post, also provide a specific image_query that describes what kind of image would be relevant for that post.

Rules:
Each post must be 280-350 words (≈ 2 200-character LinkedIn “see more” folds).
Use short, punchy paragraphs, emoji bullet points and line-breaks for scannability.
End every post with 12-18 highly-relevant hashtags: mix 4-5 big (1 M+), 4-5 mid (50 k-1 M) and 4-5 micro/niche (<50 k) hashtags.
Still output the same JSON fields: ['day'], ['posting_day'], ['content_type'], ['hook'], ['post_text'], ['hashtags'], ['cta'], ['image_query'].
"""),        
HumanMessage(
            content=f"""
NICHE: {state['niche']}
THEME: {state['content_theme']}
TONE: {state['tone']}
EXPERTISE: {state['expertise']}
AUDIENCE: {state['target_audience']}

PATTERNS:
{patterns_text}

WEB RESULTS:
DuckDuckGo: {duck}
Wikipedia: {wiki}
"""
        )
    ]

    plan = creator.invoke(messages)

    generated_posts = []
    for p in plan.posts:
        # Search for images based on the chosen approach
        image_results = search_images_pexels(
            query=p.image_query, 
            max_results=3
        )
        
        # Add small delay to avoid rate limiting
        time.sleep(0.5)
        
        generated_posts.append({
            "day": p.day,
            "posting_day": p.posting_day,
            "content_type": p.content_type,
            "hook": p.hook,
            "post_text": p.post_text,
            "hashtags": p.hashtags,
            "cta": p.cta,
            "image_query": p.image_query,
            "suggested_images": image_results
        })

    return {
        "generated_posts": generated_posts,
        "niche_summary": plan.niche_summary,
        "content_strategy": plan.content_strategy
    }

graph = StateGraph(LinkedInGrowthState)

graph.add_node("agent_a", lambda s: agent_a_auditor(s))
graph.add_node("agent_b", lambda s: agent_b_analyst(s))
graph.add_node("agent_c", lambda s: agent_c_creator(s))

graph.add_edge(START, "agent_a")
graph.add_edge("agent_a", "agent_b")
graph.add_edge("agent_b", "agent_c")
graph.add_edge("agent_c", END)

build_linkedin_growth_agent = graph.compile()
