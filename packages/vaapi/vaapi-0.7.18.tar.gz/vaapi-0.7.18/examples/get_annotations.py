"""
Fetches links to images that need their annotations validated
"""

import os
from vaapi.client import Vaapi

client = Vaapi(
    base_url=os.environ.get("VAT_API_URL"),
    api_key=os.environ.get("VAT_API_TOKEN"),
)
my_list = client.annotations.list(log=282, validated=True)
if my_list:
    print(my_list[0])

print()
print(len(my_list))