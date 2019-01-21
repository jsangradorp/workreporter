from __future__ import print_function
from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
#from trello import TrelloAPI

import requests, json
import datetime

# encoding=utf8
import sys
reload(sys)
sys.setdefaultencoding('utf8')

class GmailReporter:
    # If modifying these scopes, delete the file token.json.
    SCOPES = 'https://www.googleapis.com/auth/gmail.readonly'

    def __init__(self, token_filename, credentials_filename):
        self.authorize(token_filename, credentials_filename)
    
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
        start_date = from_datetime.isoformat().replace("-", "/")
        end_date = to_datetime.isoformat().replace("-", "/")
        q = "after:{} before:{}".format(start_date, end_date)
        results = self.service.users().messages().list(userId='me', labelIds=["SENT"], q=q).execute()
        messages = results.get('messages', [])
        report = []
        for message in messages:
            message = self.service.users().messages().get(userId="me", id=message['id']).execute()
            report.append("{} {} {}".format(filter(lambda x: x['name'] == 'Subject', message['payload']['headers'])[0]['value'], "sent to", filter(lambda x: x['name'] == 'To', message['payload']['headers'])[0]['value']))
        return report

class GCalendarReporter:
    # If modifying these scopes, delete the file token.json.
    SCOPES = 'https://www.googleapis.com/auth/calendar.readonly'

    def __init__(self, token_filename, credentials_filename):
        self.authorize(token_filename, credentials_filename)
    
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
        start_date = from_datetime.isoformat() + "T00:00:00.000Z"
        end_date = to_datetime.isoformat() + "T00:00:00.000Z"
        events_result = self.service.events().list(calendarId='primary', timeMin=start_date, timeMax=end_date,
                                            maxResults=100, singleEvents=True,
                                            orderBy='startTime').execute()
        events = events_result.get('items', [])
        report = []
        for event in events:
            report.append(event['summary'])
        return report

class TrelloReporter:

    def __init__(self, token_filename, credentials_filename):
        self.authorize(token_filename, credentials_filename)

    def authorize(self, token_filename, credentials_filename):
        creds = json.load(open(credentials_filename))
        self._apikey = creds['api_key']
        self._listid = creds['list_id']
        self._token = json.load(open(token_filename))["token"]

    def build_report(self, from_datetime, to_datetime):
        start_date = from_datetime.isoformat() + "T00:00:00.000Z"
        end_date = to_datetime.isoformat() + "T00:00:00.000Z"
        resp = requests.get("https://trello.com/1/lists/%s/cards" % (self._listid),
                params=dict(
                    key=self._apikey,
                    token=self._token,
                    since=start_date,
                    before=end_date,
                    filter='all',
                    fields='id,name,badges,labels'),
                data=None)
        resp.raise_for_status()
        return map(lambda x: x['name'], json.loads(resp.content))

class WorkReporter:

    def __init__(self):
        self.gcalreporter = GCalendarReporter('gcal_token.json', 'gcal_credentials.json')
        self.gmailreporter = GmailReporter('gmail_token.json', 'gmail_credentials.json')
        self.trelloreporter = TrelloReporter('trello_token.json', 'trello_credentials.json')

    def output_report_header(self):
        print("These are some of the things I did the last seven days:\n")

    def output_report(self):
        self.output_report_header()
        today = datetime.datetime.utcnow().date()
        yesterday = datetime.datetime.utcnow().date() - datetime.timedelta(7)
        report = []
        report += self.gcalreporter.build_report(yesterday, today)
        report += self.gmailreporter.build_report(yesterday, today)
        report += self.trelloreporter.build_report(yesterday, today)
        report.sort()
        [print(line) for line in report]

def main():
    workreporter = WorkReporter()
    workreporter.output_report()

if __name__ == '__main__':
    main()
