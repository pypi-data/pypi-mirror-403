try:
    from .db import DB
    import feedparser
except ImportError:
    from db import DB
    import feedparser
def _test_add():
    db = DB("_test_.db")

    scores = 0
   

    res2 = db.add_feed("https://lexfridmaan.com/feded/podcasst/s")
    if type(res2) == type(("data","1")):

        print("invlide Podcast added! bug!!!!")
    else:
        scores += 1
        
        
    print(db.fetch_feeds())
    print(f"add_feed test scores: {scores}/2")
    db.close()

def _test_get():
    db = DB("_test_.db")

    scores = 0
    # ++++++++++++++++++++++++++++++++++++++
    # add correct url
    res = db.fetch_feeds()
    if type(res) == type(("data", "1")) or type(res) == type([]):

        scores +=1

    print(db.fetch_feeds())
    print(f"add_feed test scores: {scores}/1")
    db.close()

import pygame
import os
import threading

def _test_play():
    pygame.mixer.init()

    def play_audio():
        pygame.mixer.init()
        pygame.mixer.music.load(os.path.join(os.path.dirname(os.path.dirname(__file__)), "test.mp3"))
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)

    threading.Thread(target=play_audio, daemon=True).start()


def test():

    print("test")

    # add rss feed url
    feed_url = input("add fedd url : ")

    # extrack data from feedprase
    feed = feedparser.parse(feed_url)

    # for i in feed.entries:
    #     print("-" * 32)
    #     print(f"Episode: {i.title}")
    #     print(f"Audio URL: {i.enclosures[0].href}")
    #     print(f"Published: {i.published}")
    #     print(f"Summary: {i.summary}")
    #     print(f"Author: {i.author}")
    #     print("-" * 32)

    print(feed.entries[0])

    print("ur podcast is ready go spotify and listentd :D ")


import requests 
import io
# def _test_chunk_down(url, chunk_duration_sec=3255):
#     with requests.get(url,  stream=True) as r:
#         buffer = io.BytesIO()
#         ccumulated = 0
#         chunk_size = int(44100 * 2 * 2 * chunk_duration_sec)


if __name__ == "__main__":
    print("test")
    # _test_chunk_down(
    #     "https://media.blubrry.com/takeituneasy/content.blubrry.com/takeituneasy/mit_ai_max_tegmark.mp3"
    # )

    # _test_add()
    # _test_get()
    # _test_play()
    test()
