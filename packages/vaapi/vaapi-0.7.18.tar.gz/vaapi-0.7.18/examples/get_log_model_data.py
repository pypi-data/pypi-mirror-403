from vaapi.client import Vaapi
import os

def get_log1():
    response = client.logs.list()
    for log in response:
        print(log)

def get_log2():
    response = client.logs.list(game=96)
    for log in response:
        print(log)

    # TODO: show other ways of querying

if __name__ == "__main__":
    client = Vaapi(
        base_url=os.environ.get("VAT_API_URL"),
        api_key=os.environ.get("VAT_API_TOKEN"),
    )

    get_log1()
    get_log2()