import os
from vaapi.client import Vaapi



if __name__ == "__main__":
    client = Vaapi(
        base_url=os.environ.get("VAT_API_URL"),
        api_key=os.environ.get("VAT_API_TOKEN"),
    )
    response = client.team.list()
    print(response)
    
    client.team.create(team_id=333,name='New Robots')
    
    response = client.team.list()
    print(response)


