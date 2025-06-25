# share.py

import os
import feedparser
import requests
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

    # title + url
    title = entry.title
    url   = entry.link

    # summary HTML → plain text excerpt
    html    = entry.get("summary", "")
    text    = BeautifulSoup(html, "html.parser").get_text()
    excerpt = text.strip().split("\n")[0][:200]  # first line, 200 chars

    # up to 6 hashtags from <category>
    tags     = [t.term for t in entry.get("tags", [])]
    hashtags = ["#" + t.strip().title().replace(" ", "") for t in tags[:6]]

    # cover-image from <figure><img>
    raw_html    = entry.get("content", [{}])[0].get("value", "")
    img_tag     = BeautifulSoup(raw_html, "html.parser").find("img")
    cover_image = img_tag["src"] if img_tag and img_tag.has_attr("src") else None

    return title, url, excerpt, hashtags, cover_image

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
    "AI":          ["ai","machine learning","deep learning"],
    "Programming": ["programming","code","development","python","java","c "],
    "Web Dev":     ["web","html","css","javascript","react","node"],
    "Career":      ["career","job","interview","resume"]
}
def detect_category(title):
    t = title.lower()
    for cat, kws in CATEGORY_KEYWORDS.items():
        if any(kw in t for kw in kws):
            return cat
    return "General"

# 4. Weekday-tuned language
WEEKDAY_INTROS = {
    0: "Kickstart your week with",
    1: "Take your Tuesday further with",
    2: "Midweek read:",
    3: "Almost Friday! Check out",
    4: "Wrap your week with",
    5: "Perfect weekend read:",
    6: "Sunday insights:"
}

# 5. Category-tone sentences
CATEGORY_INTROS = {
    "AI":          "Explore cutting-edge AI insights",
    "Programming": "Sharpen your programming skills",
    "Web Dev":     "Dive into web development",
    "Career":      "Boost your career journey",
    "General":     "Check out this post"
}

# 6. Comment prompts
COMMENT_PROMPTS = [
    "What’s your experience with this?",
    "Drop your thoughts below 👇",
    "Have questions? Ask away!",
    "How will you apply this?"
]

# 7. Build the post text
def compose_post(title, url, excerpt, hashtags):
    wd         = datetime.now().weekday()
    week_intro = WEEKDAY_INTROS.get(wd, "Check out")
    cat        = detect_category(title)
    cat_intro  = CATEGORY_INTROS.get(cat, CATEGORY_INTROS["General"])
    comment    = COMMENT_PROMPTS[hash(title) % len(COMMENT_PROMPTS)]

    text = (
        f"{week_intro} {cat_intro} \"{title}\"? 🚀\n\n"
        f"{excerpt}...\n\n"
        f"{url}\n\n"
        f"{comment}"
    )

    if hashtags:
        text += "\n\n" + " ".join(hashtags)

    return text

# 8. Publish to LinkedIn
def share_linkedin(text, article_url, cover_image=None):
    media_block = [{"status":"READY", "originalUrl": article_url}]
    if cover_image:
        media_block.append({"status":"READY", "originalUrl": cover_image})

    payload = {
        "author": LI_ACTOR,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary":    {"text": text},
                "shareMediaCategory": "ARTICLE",
                "media":              media_block
            }
        },
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"}
    }
    headers = {
        "Authorization":           f"Bearer {LI_TOKEN}",
        "Content-Type":            "application/json",
        "X-Restli-Protocol-Version": "2.0.0"
    }
    resp = requests.post("https://api.linkedin.com/v2/ugcPosts",
                         headers=headers, json=payload)
    resp.raise_for_status()

# 9. Main
if __name__ == "__main__":
    title, url, excerpt, hashtags, cover_image = get_latest()

    if url == read_last():
        print("🟢 No new post.")
        exit()

    post_text = compose_post(title, url, excerpt, hashtags)
    try:
        share_linkedin(post_text, url, cover_image)
        print("✅ Posted to LinkedIn!")
    except Exception as e:
        print("❌ Post failed:", e)
        exit()

    write_last(url)
