import os
import pickle
import sys

# Redirect stdout and stderr to a file in the workspace
sys.stdout = open('auth_output.txt', 'w', buffering=1)
sys.stderr = sys.stdout

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/drive']

def authenticate_google_drive():
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time.
    if os.path.exists('token.pickle'):
        try:
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        except Exception as e:
            print("Failed to load existing token:", e)
            
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Refreshing access token...")
            try:
                creds.refresh(Request())
            except Exception as e:
                print("Failed to refresh token:", e)
                creds = None
                
        if not creds:
            print("Starting authentication flow...")
            client_secret_file = 'client_secret_151020669146-dju4hsb1ve4beo53a11l8h6k4v7v8khk.apps.googleusercontent.com.json'
            flow = InstalledAppFlow.from_client_secrets_file(client_secret_file, SCOPES)
            # Port 0 means find an open port.
            creds = flow.run_local_server(port=0)
            
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
            print("Token saved to token.pickle")
            
    return creds

def test_drive():
    try:
        creds = authenticate_google_drive()
        service = build('drive', 'v3', credentials=creds)
        
        # Call the Drive v3 API
        print("Fetching files/folders in Drive...")
        results = service.files().list(
            pageSize=10, fields="nextPageToken, files(id, name)").execute()
        items = results.get('files', [])

        if not items:
            print('No files found.')
        else:
            print('Files:')
            for item in items:
                print(f"{item['name']} ({item['id']})")
    except Exception as e:
        print("An error occurred during Google Drive API call:", e)

if __name__ == "__main__":
    test_drive()
