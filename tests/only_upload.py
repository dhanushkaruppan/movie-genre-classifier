import os
import pickle
import sys
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request

def get_credentials():
    creds = None
    if os.path.exists('token.pickle'):
        try:
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        except Exception as e:
            print("Failed to load token.pickle:", e)
            
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Refreshing credentials...")
            try:
                creds.refresh(Request())
            except Exception as e:
                print("Failed to refresh token:", e)
                creds = None
        else:
            print("Error: No valid credentials found.")
            sys.exit(1)
            
    return creds

def upload_to_drive(file_path, mime_type="application/zip"):
    creds = get_credentials()
    service = build('drive', 'v3', credentials=creds)
    
    file_metadata = {'name': os.path.basename(file_path)}
    media = MediaFileUpload(file_path, mimetype=mime_type, resumable=True)
    
    print(f"Uploading {file_path} to Google Drive...")
    try:
        request = service.files().create(body=file_metadata, media_body=media, fields='id')
        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                print(f"Upload progress: {int(status.progress() * 100)}%")
        print(f"Upload complete! File ID: {response.get('id')}")
        return response.get('id')
    except Exception as e:
        print("An error occurred during upload:", e)
        sys.exit(1)

if __name__ == "__main__":
    output_zip = "Movie_Posters_IMDb.zip"
    if os.path.exists(output_zip):
        upload_to_drive(output_zip)
    else:
        print(f"Error: {output_zip} does not exist. Please run zip_and_upload_imdb.py instead.")
