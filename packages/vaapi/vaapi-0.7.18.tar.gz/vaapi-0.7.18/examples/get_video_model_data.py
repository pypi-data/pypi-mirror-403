from vaapi.client import Vaapi
import os


def get_logs1():
    response = client.video.list()
    for video in response:
        print(video)

def get_logs2():
    response = client.video.list(type="PiCam")
    for video in response:
        print(video)

def get_logs3():
    response = client.video.list(type="GoPro")
    for video in response:
        print(video)

def get_logs4():
    response = client.video.list(game=96)
    for video in response:
        print(video)


if __name__ == "__main__":
    client = Vaapi(
        base_url=os.environ.get("VAT_API_URL"),
        api_key=os.environ.get("VAT_API_TOKEN"),
    )

    get_logs1()
    get_logs2()
    get_logs3()
    get_logs4()
