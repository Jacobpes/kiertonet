### Search Agent for kiertonet.fi and huutomylly.fi

## Use the search agent with your own search query:
1. Install dependencies: `pip install -r requirements.txt`
2. Search for what you want on kiertonet.fi
3. Inspect the page and go to network and find the url that contains "filter"
4. Copy the url and paste it in the beginning in main.py to the URL_SEARCHAGENT variable
5. Set your smtp server details in the .env file, you can see in the main.py file the variables you need to set.
6. Run the script: `python main.py`
7. Let the script run in the background and enjoy knowing about the new items!