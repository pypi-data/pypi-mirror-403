#!/usr/bin/python3
# sends an email over 465/SSL
# 
# usage: gakomail.py [-h] [-s SMTP_SERVER] [-e SENDER_EMAIL] [-p SENDER_PASSWORD] [-r RECEIVER_EMAIL] [-sub SUBJECT] [-m MESSAGE] [-l LIST]
# 
# options:
#   -h, --help            show this help message and exit
#   -s SMTP_SERVER, --smtp_server SMTP_SERVER
#                         SMTP server
#   -e SENDER_EMAIL, --sender_email SENDER_EMAIL
#                         Sender email
#   -p SENDER_PASSWORD, --sender_password SENDER_PASSWORD
#                         Sender password
#   -r RECEIVER_EMAIL, --receiver_email RECEIVER_EMAIL
#                         Receiver email
#   -sub SUBJECT, --subject SUBJECT
#                         Email subject
#   -m MESSAGE, --message MESSAGE
#                         Email message content
#   -l LIST, --list LIST  Adds list-id header

  
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import argparse
import hashlib
import keyring
import sys
import os
from datetime import datetime
login_keyring=keyring.get_keyring()

# default server
SMTP_SERVER='example.com'
SMTP_USER='jane@example.com'
DEFAULT_RECIPIENT='jane@example.com'

# Load defaults from .env file if it exists
def load_env_defaults():
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    if key == 'SMTP_SERVER':
                        globals()['SMTP_SERVER'] = value
                    elif key == 'SMTP_USER':
                        globals()['SMTP_USER'] = value
                    elif key == 'DEFAULT_RECIPIENT':
                        globals()['DEFAULT_RECIPIENT'] = value

load_env_defaults()

print(f"Using SMTP_SERVER={SMTP_SERVER}, SMTP_USER={SMTP_USER}, DEFAULT_RECIPIENT={DEFAULT_RECIPIENT}")

class EmailArgs:
    def __init__(self):
        self.sender_email = None
        self.sender_password = None
        self.receiver_email = ""
        self.bcc = ""
        self.subject = None
        self.message = None
        self.smtp_server = SMTP_SERVER
        self.list = False
        
def send_email(args):
    """
       send an email in MIME format
    """

    message_type = "unknown message_type"

    # Add body to the email
    if args.message.startswith("From: ") \
        or args.message.startswith("Content-Type: multipart/alternative")\
        :
        raw_email_to_be_sent = args.message
        message_type = "raw"
    else:
        message_type = "MIMEMultipart"

        # we construct a message
        # Create a multipart message and set headers
        email = MIMEMultipart()
        email["From"] = args.sender_email
        email["To"] = args.receiver_email
        email["Subject"] = args.subject
        
        # for deltachat, list-id works
        # for thunderbird list-id does not work see https://bugzilla.mozilla.org/show_bug.cgi?id=1930358, one option is to use "References" or "In-Reply-To" or "Chat-Group-Id"
        if args.list == True or args.list == "True":
            email["List-id"] = args.subject+ " <"+hashlib.sha256((args.sender_email+args.receiver_email+args.subject).encode()).hexdigest()+">"
        if isinstance(args.list, str) and args.list != "True" and args.list != "False" :
            email["List-id"] = args.list + " <" + hashlib.sha256(args.list.encode()).hexdigest() + ">"

        if args.message.startswith("<html>"):
            content_type = "html"
            email.attach(MIMEText(args.message, content_type))
            raw_email_to_be_sent = email.as_string()
        elif args.message.startswith("BEGIN:VCALENDAR"):
            content_type = "calendar"
            # KTH SpamAssassin hates invitations with empty message, so we add one
            email.attach(MIMEText("please see the calendar invitation attached", "plain"))
            email.attach(MIMEText(args.message, content_type))
            raw_email_to_be_sent = email.as_string()
        else:
            # default, plain text
            email.attach(MIMEText(args.message, "plain"))
            raw_email_to_be_sent = \
f"""From: {args.sender_email}
To: {args.receiver_email}
Subject: {args.subject}

{args.message}
"""            
    

    # Create SMTP session for sending the email
    with smtplib.SMTP_SSL(args.smtp_server, 465) as server:
        server.login(args.sender_email, args.sender_password)
        for r in args.receiver_email.split(",") + args.bcc.split(","):
            r = r.strip()
            if len(r)==0: continue
            try:
                # print(r)
                server.sendmail(args.sender_email, r, raw_email_to_be_sent)
                print("gakomail.py",message_type,"sent to ",r)
                try:
                    log_file_path = os.path.expanduser("~/.cache/gakomail.log")
                    os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
                    with open(log_file_path, "a") as log_file:
                        log_file.write(f"{datetime.now().isoformat()} - To: {r}, Subject: {args.subject}\n")
                except Exception as log_e:
                    print(f"Failed to write to log file: {log_e}", file=sys.stderr)

            except Exception as e:
                print("cannot send to ",r, file=sys.stderr)
                raise e


#def send_email(smtp_server, sender_email, sender_password, receiver_email, subject, message):
    ## Create a multipart message and set headers
    #email = MIMEMultipart()
    #email["From"] = sender_email
    #email["To"] = receiver_email
    #email["Subject"] = subject

    ## Add body to the email
    #email.attach(MIMEText(message, "plain"))

    ## Create SMTP session for sending the email
    #with smtplib.SMTP(smtp_server, 465) as server:
        #server.starttls()
        #server.login(sender_email, sender_password)
        #server.sendmail(sender_email, receiver_email, email.as_string())

def parse_and_send_email():
    # Create an ArgumentParser object
    parser = argparse.ArgumentParser()
    # Add arguments to the parser with default values
    parser.add_argument('-s', '--smtp_server', default=SMTP_SERVER, help='SMTP server')
    parser.add_argument('-e', '--sender_email', default=SMTP_USER, help='Sender email')
    parser.add_argument('-p', '--sender_password', default=login_keyring.get_password('login2', SMTP_USER), help='Sender password')
    
    # recipients
    parser.add_argument('-r', '--receiver_email', default=DEFAULT_RECIPIENT, help='Receiver email')
    parser.add_argument('-b', '--bcc', default='', help='BCC email')

    parser.add_argument('-sub', '--subject', default='Hello from gakomail.py!', help='Email subject')
    parser.add_argument('-m', '--message', default='This is a test email sent using Python.', help='Email message content')
    parser.add_argument('-l', '--list', default=True, help='Adds list-id header')

    # Parse the arguments
    args = parser.parse_args()

    # Send the email
    send_email(args)

if __name__ == '__main__':
    parse_and_send_email()
