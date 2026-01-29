from vaapi.client import Vaapi
import os

def get_all_states_for_option():
    behavior_option = client.behavior_option.list(log=282,option_name="fall_down_and_stand_up")
    behavior_option_states = client.behavior_option_state.list(log=282,option_id=behavior_option[0].id)
    print(behavior_option_states)

if __name__ == "__main__":
    client = Vaapi(
        base_url=os.environ.get("VAT_API_URL"),
        api_key=os.environ.get("VAT_API_TOKEN"),
    )
    get_all_states_for_option()