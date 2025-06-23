import os, json
import feedparser, requests

# 1. Env-configured settings
RSS_URL   = os.environ["MEDIUM_RSS_URL"]
LI_TOKEN  = os.environ["LINKEDIN_ACCESS_TOKEN"]
LI_ACTOR  = os.environ["LINKEDIN_ACTOR_URN"]
LAST_FILE = "last.txt"

# 2. Fetch latest Medium post
def get_latest():
    feed = feedparser.parse(RSS_URL)
    return feed.entries[0].link

# 3. Persist last-seen post
def read_last():
    try:
        return open(LAST_FILE).read().strip()
    except FileNotFoundError:
        return ""

def write_last(url):
    with open(LAST_FILE, "w") as f:
        f.write(url)

# 4. LinkedIn API call
def share_linkedin(url):
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
                "shareCommentary": {"text": f"Check out my new blog! {url}"},
                "shareMediaCategory": "ARTICLE",
                "media": [{"status": "READY", "originalUrl": url}]
            }
        },
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"}
    }
    r = requests.post(
        "https://api.linkedin.com/v2/ugcPosts",
        headers=headers,
        json=payload
    )
    r.raise_for_status()
    print(f"✅ Shared to LinkedIn: {url}")

# 5. Main agent logic
def main():
    latest = get_latest()
    if latest != read_last():
        try:
            share_linkedin(latest)
        except Exception as e:
            print(f"❌ LinkedIn post failed: {e}")
            return
        write_last(latest)
    else:
        print("🟢 No new post to share.")

if __name__ == "__main__":
    main()
