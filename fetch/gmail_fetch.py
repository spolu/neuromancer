import base64
import re

from apiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools

SCOPES = 'https://www.googleapis.com/auth/gmail.readonly'
store = file.Storage('./fetch/credentials.json')
creds = store.get()
if not creds or creds.invalid:
    flow = client.flow_from_clientsecrets('./fetch/client_secret.json', SCOPES)
    args = tools.argparser.parse_args()
    args.noauth_local_webserver = True
    creds = tools.run_flow(flow, store, args)
service = build('gmail', 'v1', http=creds.authorize(Http()))

def retrieve_labels(labels):
    messages = []

    print("Retrieving initial page")
    response = service.users().messages().list(
        userId='me',
        maxResults=500,
        labelIds=labels,
    ).execute()
    if 'messages' in response:
        messages.extend(response['messages'])

    while 'nextPageToken' in response:
        print("Retrieving page: page_token={}".format(response['nextPageToken']))
        response = service.users().messages().list(
            userId='me',
            maxResults=500,
            labelIds=labels,
            pageToken=response['nextPageToken'],
        ).execute()
        if 'messages' in response:
            messages.extend(response['messages'])

    return messages

messages = retrieve_labels(['SENT'])

msg_count = 0

with open('gmail.raw', 'w+') as f:
    for m in messages:
        body = ''
        message = service.users().messages().get(userId='me', id=m['id'], format='full').execute()
        if message['payload']['mimeType'] == 'multipart/alternative':
            for p in message['payload']['parts']:
                if p['mimeType'] == 'text/plain':
                    body = base64.urlsafe_b64decode(p['body']['data']).decode('UTF-8')
                    break
        elif message['payload']['mimeType'] == 'text/plain':
            body = base64.urlsafe_b64decode(message['payload']['body']['data']).decode('UTF-8')
        else:
            continue


        lines = body.split('\r\n')

        f.write('<START>\n')
        for l in lines:
            f.write(l + '\n')
        f.write('<END>\n')

        print("Dumping message: msg_count={}/{}".format(
            msg_count,
            len(messages),
        ))
        msg_count += 1
