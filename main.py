import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
import time
import os
from dotenv import load_dotenv
 
load_dotenv()

URL_SEARCHAGENT = "https://kiertonet.fi/filter-auctions?page=1&search=teklab&hide_ended=0&only_sold_to_highest=0&iframe=false&scope=&scope_param="

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


def send_email(subject, body):
    print("sending email:", subject, body)
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECEIVER_EMAIL
    msg['Subject'] = subject

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


def searchAgent():
    response_json = requests.get(URL_SEARCHAGENT)
    data = response_json.json().get('data')
    print("found", len(data), "items that match the search!")
    new_item = False
    for index, item in enumerate(data):
        # get item_id and convert it to string
        item_id = str(item.get('id'))
        if item_id not in item_id_memory:
            new_item = True
            print("""--------------------------------
                SEARCH AGENT FOUND NEW ITEMS
                """)

            print("ITEM", index + 1)
            print("item", item)

            interesting_data = ['id', 'title', 'highest_bid', 'is_sold_to_highest_bidder', 'fullUrl']
            item_details = []
            for article in interesting_data:
                if article == 'fullUrl': 
                    # print link in blue
                    print(article, ":", "\033[94m" + item.get(article) + "\033[0m")
                    item_details.append(f"{article}: {item.get(article)}")
                else:
                    item_details.append(f"{article}: {item.get(article)}")

            # Prepare email content
            subject = "New Item Found by Search Agent" + item.get('title') + " - " + item.get('fullUrl')
            body = "\n".join(item_details)

            # Send the email
            success = send_email(subject, body)
            if success:
                item_id_memory.append(str(item.get('id')))
                # write item_id_memory to file
                with open('item_id_memory.txt', 'w') as file:
                    file.write(','.join(map(str, item_id_memory)))
                # close file
                file.close()
                print("Email sent successfully!")
    if new_item == False:
        print("No new items found")

# Set timeout to call searchAgent every minute to see if there are new items
while True:
    searchAgent()
    time.sleep(600) # wait 10 minutes before calling searchAgent again