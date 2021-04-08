import json
import requests
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

GS_SPREADSHEET_ID = os.environ['GS_SPREADSHEET_ID']
GS_RANGE_NAME = os.environ['GS_RANGE_NAME']
GS_CREDENTIALS_INFO = json.loads(os.environ['GS_CREDENTIALS_INFO'])

GH_URL = os.environ['GH_URL']
GH_TOKEN = os.environ['GH_TOKEN']


def main():
    creds = Credentials.from_authorized_user_info(GS_CREDENTIALS_INFO, SCOPES)
    creds.refresh(Request())

    service = build('sheets', 'v4', credentials=creds)
    sheet = service.spreadsheets()

    sheet_metadata = sheet.get(spreadsheetId=GS_SPREADSHEET_ID).execute()
    sheets = sheet_metadata.get('sheets', '')
    sheet_id = sheets[0].get("properties", {}).get("sheetId", 0)
    sheet_emails = sheets[1].get("properties", {}).get("title")

    result = sheet.values().get(
        spreadsheetId=GS_SPREADSHEET_ID, range=GS_RANGE_NAME).execute()
    values = result.get('values', [])

    emails = []
    images = []
    for row in values:
        images.append(row[0])
        emails.append([row[0], row[2]])
    
    schedule_jobs(images)
    remove_rows(service, images, sheet_id)
    save_emails(service, emails, sheet_emails)


def remove_rows(service, images, sheet_id):
    spreadsheet_data = [
        {
            "deleteDimension": {
                "range": {
                    "sheetId": sheet_id,
                    "dimension": "ROWS",
                    "startIndex": 1,
                    "endIndex": len(images)+1
                }
            }
        }
    ]
    update_spreadsheet_data = {"requests": spreadsheet_data} # Modified
    updating = service.spreadsheets().batchUpdate(
        spreadsheetId=GS_SPREADSHEET_ID, body=update_spreadsheet_data)
    updating.execute()

def save_emails(service, emails, sheet_emails):
    body = {'values': emails}
    result = service.spreadsheets().values().append(
        spreadsheetId=GS_SPREADSHEET_ID, range=sheet_emails,
        valueInputOption='USER_ENTERED', body=body).execute()

def schedule_jobs(images):
    for image in images:
        payload = {"event_type": "vilicus_scan", "client_payload": {"image":image}}
        headers = {
            'Accept': 'application/vnd.github.everest-preview+json',
            'Authorization': 'token {}'.format(GH_TOKEN)
        }
        requests.post(GH_URL, data=json.dumps(payload), headers=headers)


if __name__ == '__main__':
    main()