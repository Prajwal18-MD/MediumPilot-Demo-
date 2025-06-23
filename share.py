# share.py

import os, re, random
import feedparser, requests, markovify

# ENV
RSS_URL   = os.environ["MEDIUM_RSS_URL"]
LI_TOKEN  = os.environ["LINKEDIN_ACCESS_TOKEN"]
LI_ACTOR  = os.environ["LINKEDIN_ACTOR_URN"]
LAST_FILE = "last.txt"
INTRO_FILE = "intros.txt"

# Load Markov model
with open("model.json", encoding="utf-8") as f:
    markov_model = markovify.Text.from_json(f.read())

# Fallback templates
TEMPLATES = [
    "Ready to dive into",
    "Unlock the secrets of",
    "Discover why",
    "Level up your skills with",
    "Want to master",
    "Get started with"
]

# Stop-words for hashtags
STOPWORDS = {"the","and","in","of","to","a","for","on","with","my","your"}

def extract_hashtags(title, max_tags=3):
    words = re.findall(r"\b\w+\b", title)
    candidates = [w for w in words if len(w)>=4 and w.lower() not in STOPWORDS]
    seen, tags = set(), []
    for w in candidates:
        tag = w.capitalize()
        if tag.lower() not in seen:
            tags.append("#" + tag)
            seen.add(tag.lower())
        if len(tags) >= max_tags:
            break
    return " ".join(tags)

def make_intro(title):
    for _ in range(3):
        sent = markov_model.make_sentence(max_words=10, tries=5)
        if sent:
            return sent.rstrip(".!?")
    return f"{random.choice(TEMPLATES)} \"{title}\""

def append_intro(intro):
    with open(INTRO_FILE, "a", encoding="utf-8") as f:
        f.write(intro + "\n")

def get_latest():
    feed = feedparser.parse(RSS_URL)
    entry = feed.entries[0]
    return entry.title, entry.link

def read_last():
    try:
        return open(LAST_FILE, "r", encoding="utf-8").read().strip()
    except FileNotFoundError:
        return ""

def write_last(url):
    with open(LAST_FILE, "w", encoding="utf-8") as f:
        f.write(url)

def share_linkedin(intro, hashtags, url):
    text = f"{intro}? 🚀 {url}\n\n{hashtags}"
    headers = {
        "Authorization": f"Bearer {LI_TOKEN}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0"
    }
    payload = {
        "author": LI_ACTOR,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": text},
                "shareMediaCategory": "ARTICLE",
                "media": [{"status": "READY", "originalUrl": url}]
            }
        },
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"}
    }
    r = requests.post("https://api.linkedin.com/v2/ugcPosts",
                      headers=headers, json=payload)
    r.raise_for_status()
    print(f"✅ Posted: {intro}")

def main():
    title, url = get_latest()
    if url == read_last():
        print("🟢 No new post.")
        return

    intro = make_intro(title)
    hashtags = extract_hashtags(title)
    try:
        share_linkedin(intro, hashtags, url)
    except Exception as e:
        print("❌ Failed to post:", e)
        return

    write_last(url)
    append_intro(intro)

if __name__ == "__main__":
    main()
