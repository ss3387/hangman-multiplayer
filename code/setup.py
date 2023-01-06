from setuptools import setup
#kill -9 "$(pgrep ngrok)"
APP = ['hangman.py']
OPTIONS = {}

setup(
    app=APP,
    options={'py2app': OPTIONS},
    setup_requires=['py2app']
)