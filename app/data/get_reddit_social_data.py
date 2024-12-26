import requests
import requests.auth
from dotenv import load_dotenv
import os
import pandas as pd
from datetime import datetime
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from datetime import datetime as dt
from collections import Counter
import time
import io
from app.models import SentimentData
from app.databse import get_db


# Initialize VADER sentiment analyzer
sia = SentimentIntensityAnalyzer()
load_dotenv('./app/core/.env')
db = get_db()

def get_sentiment(text):
    return sia.polarity_scores(text)['compound']

def get_reddit_token():
    reddit_password = os.getenv('REDDIT_PASS')
    reddit_username = os.getenv('REDDIT_USER')
    client_id = os.getenv("REDDIT_CLIENT_ID")
    client_secret = os.getenv("REDDIT_SECRET_KEY")
    client_auth = requests.auth.HTTPBasicAuth(client_id, client_secret)
    post_data = {"grant_type": "password", "username": reddit_username, "password": reddit_password}
    headers = {"User-Agent": f"SentimentAnalysisBot/0.1 by {reddit_username}"}
    response = requests.post("https://www.reddit.com/api/v1/access_token", auth=client_auth, data=post_data, headers=headers)
    return response.json()['access_token']

def get_reddit_data(token, crypto='Bitcoin', subreddits=['CryptoCurrency', 'CryptoMarkets']):
    username = os.getenv('REDDIT_USER')
    headers = {"Authorization": f"bearer {token}", "User-Agent": f"SentimentAnalysisBot/0.1 by {username}"}
    params = {"limit": 100}  # Increased from 10 to 100
    subreddits.append(crypto)
    all_posts_data = []
    for subreddit in subreddits:
        try:
            response = requests.get(f"https://oauth.reddit.com/r/{subreddit}/hot", headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            for post in data['data']['children']:
                title = clean_text(post['data']['title'])
                selftext = clean_text(post['data'].get('selftext', ''))
                url = f"https://www.reddit.com{post['data']['permalink']}"
                full_text = f"{title} {selftext}"
                sentiment = get_sentiment(full_text)
                all_posts_data.append({
                    'subreddit': subreddit,
                    'title': title,
                    'selftext': selftext[:100],
                    'url': url,
                    'sentiment': sentiment,
                    'upvotes': post['data']['score'],
                    'created_at': datetime.fromtimestamp(post['data']['created_utc']).strftime("%Y-%m-%d %H:%M:%S")
                })  
            time.sleep(2)  # To respect Reddit's rate limits
        except requests.exceptions.RequestException as e:
            print(f"Error collecting data from r/{subreddit}: {str(e)}")
    store_data(all_posts_data)
    return all_posts_data
    
def store_data(posts_data):
    time = dt.utcnow().strftime("%m-%d-%Y %H:%M:%S")
    for post in posts_data:
        try:
            new_row = PostData(
                title:  post.title,
                subreddit: post.subreddit,
                description: post.selftext,
                url: post.url,
                sentiment: post.sentiment,
                upvotes: post.upvotes,
                created_at: time
                )
            db.add(new_row)
            db.commit()
            db.refresh(new_row)
        catch Exception as e:
            db.rollback()
            return f'Failure {e}'
    return "Successfully get and store sentiment data"

def clean_text(text):
    return ' '.join(text.split()).replace('"', "'")

if __name__ == '__main__':
    token = get_reddit_token()
    reddit_data = get_reddit_data(token)
