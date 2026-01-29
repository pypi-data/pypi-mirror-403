from vaapi.client import Vaapi
import os


def get_games1():
    response = client.games.list()
    for log in response:
        print(log)

    # TODO: show other ways of querying

if __name__ == "__main__":
    client = Vaapi(
        base_url=os.environ.get("VAT_API_URL"),
        api_key=os.environ.get("VAT_API_TOKEN"),
    )

    get_games1()
