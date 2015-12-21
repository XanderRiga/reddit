#/u/GoldenSights
import traceback
import praw # simple interface to the reddit API, also handles rate limiting of requests
import time
import sqlite3

'''USER CONFIGURATION'''

APP_ID = "QsnKKkJFGCiw2w"
APP_SECRET = "qJYelra0d3bE8pC64_Af_6F62QA"
APP_URI = "https://127.0.0.1:65010/authorize_callback"
APP_REFRESH = "48947512-hQP3hfBrpJOv9a_rd4n4i5pPJvM"
# https://www.reddit.com/comments/3cm1p8/how_to_make_your_bot_use_oauth2/
USERAGENT = "/u/xandertestbot oauth2 test"
# This is a short description of what the bot does.
# For example "Python automatic replybot v2.0 (by /u/GoldenSights)"
SUBREDDIT = "bottest"
# This is the sub or list of subs to scan for new posts. For a single sub, use "sub1". For multiple subreddits, use "sub1+sub2+sub3+..."
KEYWORDS = ["LIL JON", "lil_jon", "lil jon"]
# These are the words you are looking for
KEYAUTHORS = []
# These are the names of the authors you are looking for
# The bot will only reply to authors on this list
# Keep it empty to allow anybody.
REPLYSTRING = "WHAT?!??!?!? YEAAAA?!?!??!?!"
# This is the word you want to put in reply
MAXPOSTS = 100
# This is how many posts you want to retrieve all at once. PRAW can download 100 at a time.
WAIT = 30
# This is how many seconds you will wait between cycles. The bot is completely inactive during this time.

CLEANCYCLES = 10
# After this many cycles, the bot will clean its database
# Keeping only the latest (2*MAXPOSTS) items

'''All done!'''

try:
    import bot
    USERAGENT = bot.aG
except ImportError:
    pass

print('Opening SQL Database')
sql = sqlite3.connect('sql.db')
cur = sql.cursor()
cur.execute('CREATE TABLE IF NOT EXISTS oldposts(id TEXT)')

print('Logging in...')
r = praw.Reddit(USERAGENT)
r.set_oauth_app_info(APP_ID, APP_SECRET, APP_URI)
r.refresh_access_information(APP_REFRESH)

def replybot():
    print('Searching %s.' % SUBREDDIT)
    subreddit = r.get_subreddit(SUBREDDIT)
    posts = list(subreddit.get_comments(limit=MAXPOSTS))
    posts.reverse()
    for post in posts:
        # Anything that needs to happen every loop goes here.
        pid = post.id

        try:
            pauthor = post.author.name
        except AttributeError:
            # Author is deleted. We don't care about this post.
            continue

        if pauthor.lower() == r.user.name.lower():
            # Don't reply to yourself, robot!
            print('Will not reply to myself.')
            continue

        if KEYAUTHORS != [] and all(auth.lower() != pauthor for auth in KEYAUTHORS):
            # This post was not made by a keyauthor
            continue

        cur.execute('SELECT * FROM oldposts WHERE ID=?', [pid])
        if cur.fetchone():
            # Post is already in the database
            continue

        cur.execute('INSERT INTO oldposts VALUES(?)', [pid])
        sql.commit()
        pbody = post.body.lower()
        if any(key.lower() in pbody for key in KEYWORDS):
            print('Replying to %s by %s' % (pid, pauthor))
            try:
                post.reply(REPLYSTRING)
            except praw.requests.exceptions.HTTPError as e:
                if e.response.status_code == 403:
                    print('403 FORBIDDEN - is the bot banned from %s?' % post.subreddit.display_name)

cycles = 0
while True:
    try:
        replybot()
        cycles += 1
    except Exception as e:
        traceback.print_exc()
    if cycles >= CLEANCYCLES:
        print('Cleaning database')
        cur.execute('DELETE FROM oldposts WHERE id NOT IN (SELECT id FROM oldposts ORDER BY id DESC LIMIT ?)', [MAXPOSTS * 2])
        sql.commit()
        cycles = 0
    print('Running again in %d seconds \n' % WAIT)
    time.sleep(WAIT)

    
