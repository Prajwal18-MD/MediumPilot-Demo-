# share.py

import os, re
import feedparser, requests
from datetime import datetime
from bs4 import BeautifulSoup  

# 1. Config
RSS_URL   = os.environ["MEDIUM_RSS_URL"]
LI_TOKEN  = os.environ["LINKEDIN_ACCESS_TOKEN"]
LI_ACTOR  = os.environ["LINKEDIN_ACTOR_URN"]
LAST_FILE = "last.txt"

# 2. Helpers

def get_latest():
    feed = feedparser.parse(RSS_URL)
    entry = feed.entries[0]
    title = entry.title
    url   = entry.link
    # summary HTML → plain text
    html  = entry.get("summary", "")
    text  = BeautifulSoup(html, "html.parser").get_text()
    excerpt = text.strip().split("\n")[0][:200]  # first line, 200 chars
    return title, url, excerpt

def read_last():
    try:
        return open(LAST_FILE).read().strip()
    except FileNotFoundError:
        return ""

def write_last(u):
    with open(LAST_FILE, "w") as f:
        f.write(u)

# 3. Auto-detect topic category
CATEGORY_KEYWORDS = {
    "AI":      ["ai","machine learning","deep learning"],
    "Programming": ["programming","code","development","python","java","c "],
    "Web Dev": ["web","html","css","javascript","react","node"],
    "Career":  ["career","job","interview","resume"]
}
def detect_category(title):
    t = title.lower()
    for cat, kws in CATEGORY_KEYWORDS.items():
        for kw in kws:
            if kw in t:
                return cat
    return "General"

# 4. Weekday-tuned language
WEEKDAY_INTROS = {
    0: "Kickstart your week with",    # Monday
    1: "Take your Tuesday further with",
    2: "Midweek read:",               # Wednesday
    3: "Almost Friday! Check out",
    4: "Wrap your week with",         # Friday
    5: "Perfect weekend read:",       # Saturday
    6: "Sunday insights:"             # Sunday
}

# 5. Category-tone sentences
CATEGORY_INTROS = {
    "AI": "Explore cutting-edge AI insights",
    "Programming": "Sharpen your programming skills",
    "Web Dev": "Dive into web development",
    "Career": "Boost your career journey",
    "General": "Check out this post"
}

# 6. Comment prediction helper
COMMENT_PROMPTS = [
    "What’s your experience with this?",
    "Drop your thoughts below 👇",
    "Have questions? Ask away!",
    "How will you apply this?"
]

# 7. Compose the full post text
def compose_post(title, url, excerpt):
    # a) base phrases
    wd = datetime.now().weekday()
    week_intro = WEEKDAY_INTROS.get(wd, "Check out")
    cat = detect_category(title)
    cat_intro = CATEGORY_INTROS.get(cat, CATEGORY_INTROS["General"])

    # b) comment prompt
    comment = COMMENT_PROMPTS[hash(title) % len(COMMENT_PROMPTS)]

    # c) assemble
    text = (
        f"{week_intro} {cat_intro} \"{title}\"? 🚀\n\n"
        f"{excerpt}...\n\n"
        f"{url}\n\n"
        f"{comment}"
    )
    return text

# 8. LinkedIn post
def share_linkedin(text):
    payload = {
        "author": LI_ACTOR,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": text},
                "shareMediaCategory": "ARTICLE",
                "media": [{"status":"READY","originalUrl": excerpt_url}]
            }
        },
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"}
    }
    headers = {
        "Authorization": f"Bearer {LI_TOKEN}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0"
    }
    r = requests.post("https://api.linkedin.com/v2/ugcPosts",
                      headers=headers, json=payload)
    r.raise_for_status()

# 9. Main logic
if __name__ == "__main__":
    title, excerpt_url, excerpt = get_latest()
    if excerpt_url == read_last():
        print("🟢 No new post.")
        exit()

    post_text = compose_post(title, excerpt_url, excerpt)
    try:
        share_linkedin(post_text)
        print("✅ Posted to LinkedIn!")
    except Exception as e:
        print("❌ Post failed:", e)
        exit()

    # persist
    write_last(excerpt_url)
