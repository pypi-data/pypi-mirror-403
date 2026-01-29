#######################
#      castaway       #
#######################     
import feedparser
from .core import htmlpraser 
from .screen import CastAwayApp

def main():
   app = CastAwayApp()
   app.run()

