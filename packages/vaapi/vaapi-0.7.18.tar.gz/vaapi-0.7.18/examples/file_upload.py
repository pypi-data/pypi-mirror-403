import requests
import os

def upload_model(files):
    response = requests.post(url=f"{base_url[0]}api/upload/model/",files=files,headers=headers)
    print(response.text)

def upload_dataset(files):
    response = requests.post(url=f"{base_url[0]}api/upload/dataset/",files=files,headers=headers)
    print(response.text)

if __name__ == "__main__":
    base_url=os.environ.get("VAT_API_URL"),
    api_key=os.environ.get("VAT_API_TOKEN"),

    # specify a file you want to upload
    files = {'file': open('test-upload.h5', 'rb')} 
    headers ={"Authorization":f"Token {api_key[0]}"}

    upload_model(files)
    # upload_dataset(files)
