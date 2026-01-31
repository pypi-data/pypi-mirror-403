import platform
from setuptools import setup

requirements = [
        # cc
        'websocket-client',
        'httpx',
        'requests',
        'python-requestr',
        'python_ghost_cursor',
        'price_parser',
        
        # Mine
        'python-timeout',
        'python-printr',
        'error_alerts',
        'python-objectifier',
        
        # Socials     
        'tweepy',
        'python-twitter',     
        'praw',
        'instagrapi',
        'telethon',
        'yt-dlp',
        
        # Scraping
        'feedparser',
        'bs4',
        'python-slugify',
        'anticaptchaofficial',
        'openai',

        # Google
        'gspread',
        'google-api-python-client',
        'google_auth_oauthlib',
        'google',

        # Server
        'flask',
        'waitress',
        'requests-futures',
        
        # Misc
        'schedule',
        'demoji',
        'ffprobe-python',
        'python-dateutil',
        'dateparser',
        'pathvalidate',
        'inflect',
        'betfairlightweight',
        'websockets',
        ]

if platform.system() == 'Windows':
    requirements += [
        'python-window-recorder',
        'moviepy',
        ]

setup(
    name = 'needed_libs',
    packages = ['needed_libs'],
    version = '3.0',
    install_requires = requirements
    )