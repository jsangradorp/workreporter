from __future__ import print_function
from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools

import datetime

# encoding=utf8
import sys
reload(sys)
sys.setdefaultencoding('utf8')

class GmailReporter:
    # If modifying these scopes, delete the file token.json.
    SCOPES = 'https://www.googleapis.com/auth/gmail.readonly'

    def __init__(self):
        self.service = None
    
    def authorize(self, token_filename, credentials_filename):
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        store = file.Storage(token_filename)
        creds = store.get()
        if not creds or creds.invalid:
            # If needed, the credentials.json file needs to be obtained
            # in https://console.developers.google.com/apis/credentials?project=gmailreports-1547134468896&authuser=0
            flow = client.flow_from_clientsecrets(credentials_filename, self.SCOPES)
            creds = tools.run_flow(flow, store)
        self.service = build('gmail', 'v1', http=creds.authorize(Http()))

    def build_report(self, from_datetime, to_datetime):
        results = self.service.users().messages().list(userId='me', labelIds=["SENT"], q="after:2019/1/14 before:2019/1/15").execute()
        messages = results.get('messages', [])

        report = []
        for message in messages:
            message = self.service.users().messages().get(userId="me", id=message['id']).execute()
            report.append("{} {} {} {}".format("Sent", filter(lambda x: x['name'] == 'Subject', message['payload']['headers'])[0]['value'], "to", filter(lambda x: x['name'] == 'To', message['payload']['headers'])[0]['value']))
        return report

class GCalendarReporter:
    # If modifying these scopes, delete the file token.json.
    SCOPES = 'https://www.googleapis.com/auth/calendar.readonly'

    def __init__(self):
        self.service = None
    
    def authorize(self, token_filename, credentials_filename):
        # The file token.json stores the user's access and refresh tokens, and is     
        # created automatically when the authorization flow completes for the first   
        # time.                                                                       
        store = file.Storage(token_filename)                                            
        creds = store.get()                                                           
        if not creds or creds.invalid:                                                
            # If needed, the credentials.json file needs to be obtained               
            # in https://console.developers.google.com/apis/credentials?project=gcalreports-1547134468896&authuser=0
            flow = client.flow_from_clientsecrets(credentials_filename, self.SCOPES)         
            creds = tools.run_flow(flow, store)                                       
        self.service = build('calendar', 'v3', http=creds.authorize(Http()))               

    def build_report(self, from_datetime, to_datetime):
        events_result = self.service.events().list(calendarId='primary', timeMin=from_datetime, timeMax=to_datetime,
                                            maxResults=100, singleEvents=True,
                                            orderBy='startTime').execute()
        events = events_result.get('items', [])
        report = []
        for event in events:
            report.append(event['summary'])
        return report

class TrelloReporter:

    def build_report(self):
        pass

class WorkReporter:

    def __init__(self):
        self.gcalreporter = GCalendarReporter()
        self.gcalreporter.authorize('gcal_token.json', 'gcal_credentials.json')
        self.gmailreporter = GmailReporter()
        self.gmailreporter.authorize('gmail_token.json', 'gmail_credentials.json')

    def output_report(self):
        today = (datetime.datetime.utcnow().date()).isoformat() + 'T00:00:00.000Z' # 'Z' indicates UTC time
        yesterday = (datetime.datetime.utcnow().date() - datetime.timedelta(1)).isoformat() + 'T00:00:00.000Z' # 'Z' indicates UTC time
        print(self.gcalreporter.build_report(yesterday, today))
        print(self.gmailreporter.build_report(yesterday, today))

def main():
    workreporter = WorkReporter()
    workreporter.output_report()

if __name__ == '__main__':
    main()
