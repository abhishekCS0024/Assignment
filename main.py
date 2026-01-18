from agent import build_linkedin_growth_agent
import json
from dotenv import load_dotenv

def run_linkedin_growth_agent(
    desc: str, 
    expertise: str, 
    audience: str, 
):
    init_state = {
        "desc": desc,
        "expertise": expertise,
        "target_audience": audience,
        "messages": []
    }

    print(f"\n🚀 RUNNING LINKEDIN GROWTH AGENT ...\n")

    final = build_linkedin_growth_agent.invoke(init_state)
    return final

def display_results(state):
    print("\n\n================ FINAL CONTENT PLAN ================\n")
    print("NICHE:", state["niche_summary"])
    print("\nSTRATEGY:", state["content_strategy"])

    print("\n\n================ 5-DAY CONTENT ================\n")
    for p in state["generated_posts"]:
        print(f"\nDAY {p['day']} - {p['posting_day']}")
        print("Hook:", p["hook"])
        print("Content:", p["post_text"])
        print("Hashtags:", p["hashtags"])
        print("CTA:", p["cta"])
        print("\nImage Suggestions:")
        for i, img in enumerate(p.get("suggested_images", []), 1):
            if isinstance(img, dict):
                if 'url' in img:
                    print(f"  {i}. {img['url']}")
                    if 'source' in img:
                        print(f"     Source: {img['source']}")
                elif 'prompt' in img:
                    print(f"  {i}. AI Prompt: {img['prompt']}")
                elif 'search_url' in img:
                    print(f"  {i}. {img['platform']}: {img['search_url']}")
            else:
                print(f"  {i}. {img}")
        print("\n" + "-" * 50)

def save_results(state, f="linkedin_content_plan.json"):
    with open(f, "w", encoding="utf-8") as fp:
        json.dump(state, fp, indent=2, ensure_ascii=False)
    print(f"\n✅ Saved: {f}")

if __name__ == "__main__":
    load_dotenv()

    # Using Pexels API with your API key
    result = run_linkedin_growth_agent(
        desc="HR manager helping companies implement better hiring frameworks",
        expertise="HR, hiring, recruitment, ATS, interviewing",
        audience="Job seekers, HR professionals, recruiters",
    )

    display_results(result)
    save_results(result)