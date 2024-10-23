import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from bs4 import BeautifulSoup
import requests
import time
import os
from dotenv import load_dotenv
 
URLS_SEARCHAGENT = [
    "https://kiertonet.fi/filter-auctions?page=1&search=teklab&hide_ended=0&only_sold_to_highest=0&iframe=false&scope=&scope_param=", # teklab
    "https://kiertonet.fi/filter-auctions?page=1&search=teollisuuskone&hide_ended=1&only_sold_to_highest=0&iframe=false&scope=&scope_param=" # teollisuuskone
]
REQUEST_INTERVAL = 60 # seconds

load_dotenv()

# Email configuration
SMTP_SERVER = os.getenv('SMTP_SERVER')
SMTP_PORT = os.getenv('SMTP_PORT')
SENDER_EMAIL = os.getenv('SENDER_EMAIL')
SENDER_PASSWORD = os.getenv('SENDER_PASSWORD')
RECEIVER_EMAIL = os.getenv('RECEIVER_EMAIL')

# Print out the environment variables to debug
print(f"SMTP_SERVER: {SMTP_SERVER}")
print(f"SMTP_PORT: {SMTP_PORT}")
print(f"SENDER_EMAIL: {SENDER_EMAIL}")
print(f"RECEIVER_EMAIL: {RECEIVER_EMAIL}")
print("--------------------------------")
print("Agent is running...")

item_id_memory = []
# read item_id_memory from file of found. item_id_memory.txt separated by commas
if os.path.exists('item_id_memory.txt'):
    with open('item_id_memory.txt', 'r') as file:
        item_id_memory = file.read().split(',')
        file.close()
else:
    item_id_memory = []
    # create item_id_memory.txt
    with open('item_id_memory.txt', 'w') as file:
        file.write('')
    file.close()


def send_email(subject, body, is_html=False):
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECEIVER_EMAIL
    msg['Subject'] = subject

    # Attach the body with appropriate MIME type
    if is_html:
        msg.attach(MIMEText(body, 'html'))
    else:
        msg.attach(MIMEText(body, 'plain'))

    try:
        # Use SMTP_SSL if port is 465, otherwise use SMTP and starttls
        if SMTP_PORT == '465':
            with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
                server.login(SENDER_EMAIL, SENDER_PASSWORD)
                server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
        else:
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.ehlo()
                server.starttls()  # Secure the connection
                server.ehlo()
                server.login(SENDER_EMAIL, SENDER_PASSWORD)
                server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
        
        print("Email sent successfully!")
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        import traceback
        traceback.print_exc()
        return False


def fetch_data(url):
    response_json = requests.get(url)
    return response_json.json().get('data')

def process_item(item):
    interesting_data = ['id', 'title', 'highest_bid', 'is_sold_to_highest_bidder', 'fullUrl']
    item_details = []
    for article in interesting_data:
        if article == 'fullUrl': 
            print(article, ":", "\033[94m" + item.get(article) + "\033[0m")
            item_details.append(f"{article}: {item.get(article)}")
        else:
            item_details.append(f"{article}: {item.get(article)}")
    return item_details

def handle_new_item(item, index, item_picture_url):
    # Ensure item_id_memory is initialized
    global item_id_memory
    if 'item_id_memory' not in globals():
        item_id_memory = []

    print("""--------------------------------
        SEARCH AGENT FOUND NEW ITEMS
        """)
    print("ITEM", index + 1)
    print("item", item)

    item_details = process_item(item)
    subject = "New Item Found by Search Agent: " + item.get('title') + " - " + item.get('fullUrl')
    
    # Ensure the item_picture_url is properly formatted
    body_html = f"""
    <html>
        <body>
            <p>New item found:</p>
            <p>{'<br>'.join(item_details)}</p>
            <p>Check out the image below:</p>
            <img src="{item_picture_url}" alt="Item Image" style="max-width:600px;">
        </body>
    </html>
    """

    success = send_email(subject, body_html, is_html=True)
    
    if success:
        item_id_memory.append(str(item.get('id')))
        item_id_memory = list(set(item_id_memory))
        with open('item_id_memory.txt', 'w') as file:
            file.write(','.join(map(str, item_id_memory)))
        print("Email sent successfully!")


def searchAgent(url):
    data = fetch_data(url)
    # print("found", len(data), "items that match the search!")
    new_item = False
    for index, item in enumerate(data):
        item_id = str(item.get('id'))
        if item_id not in item_id_memory:
            new_item = True
            item_picture_url = getItemPictureUrl(item.get('fullUrl'))
            print("item_picture_url", item_picture_url)
            handle_new_item(item, index, item_picture_url)
    # if not new_item:
        # print("No new items found")

def getItemPictureUrl(url):
    response = requests.get(url)

    soup = BeautifulSoup(response.text, 'html.parser')
    image_url = soup.find('meta', property="og:image").get('content')
    return image_url


# Set timeout to call searchAgent every minute to see if there are new items
while True:
    for url in URLS_SEARCHAGENT:
        searchAgent(url)
    time.sleep(REQUEST_INTERVAL)
