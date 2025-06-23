import os, json
import feedparser, requests

# 1. Env-configured settings
RSS_URL   = os.environ["MEDIUM_RSS_URL"]
TW_BEARER = os.environ["TWITTER_BEARER_TOKEN"]
LI_TOKEN  = os.environ["LINKEDIN_ACCESS_TOKEN"]
LI_ACTOR  = os.environ["LINKEDIN_ACTOR_URN"]
LAST_FILE = "last.txt"

# 2. Fetch latest Medium post
def get_latest():
    feed = feedparser.parse(RSS_URL)
    return feed.entries[0].link

# 3. Persist last-seen post
def read_last():
    try: return open(LAST_FILE).read().strip()
    except: return ""
def write_last(u):
    with open(LAST_FILE,"w") as f: f.write(u)

# 4. Twitter API call
def share_twitter(url):
    hdr = {"Authorization":f"Bearer {TW_BEARER}"}
    payload = {"text": f"Check out my new blog! {url}"}
    r = requests.post("https://api.twitter.com/2/tweets",
                      json=payload, headers=hdr)
    r.raise_for_status()

# 5. LinkedIn API call
def share_linkedin(url):
    hdr = {
      "Authorization": f"Bearer {LI_TOKEN}",
      "Content-Type": "application/json",
      "X-Restli-Protocol-Version": "2.0.0"
    }
    post = {
      "author": LI_ACTOR,
      "lifecycleState": "PUBLISHED",
      "specificContent": {
        "com.linkedin.ugc.ShareContent": {
          "shareCommentary": { "text": f"Check out my new blog! {url}" },
          "shareMediaCategory": "ARTICLE",
          "media": [{
            "status": "READY",
            "originalUrl": url
          }]
        }
      },
      "visibility": { "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC" }
    }
    r = requests.post("https://api.linkedin.com/v2/ugcPosts",
                      headers=hdr, data=json.dumps(post))
    r.raise_for_status()

# 6. Main agent logic
def main():
    latest = get_latest()
    if latest != read_last():
        share_twitter(latest)
        share_linkedin(latest)
        write_last(latest)

if __name__=="__main__":
    main()
