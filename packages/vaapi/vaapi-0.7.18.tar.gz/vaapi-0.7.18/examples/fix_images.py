from vaapi.client import Vaapi
import os

if __name__ == "__main__":
    client = Vaapi(
        base_url=os.environ.get("VAT_API_URL"),
        api_key=os.environ.get("VAT_API_TOKEN"),
    )

    img_generator = client.image.list(limit=100)
    print(img_generator.count)

    image_data = list()
    for idx, img in enumerate(img_generator):
        #print(img.image_url)
        new_url = img.image_url.replace("_BerlinUnited_", "_Berlin United_")
        new_url = new_url.replace("_SPQR_", "_SPQR Team_")
        new_url = new_url.replace("_empty_", "_Invisibles_")
        new_url = new_url.replace("_NaoDevils_", "_Nao Devils_")
        new_url = new_url.replace("_Runswift_", "_rUNSWift_")
        new_url = new_url.replace("_Roboeirean_", "_RoboEireann_")
        new_url = new_url.replace("_Nomadz_", "_NomadZ_")
        new_url = new_url.replace("_HTWK_", "_HTWK Robots_")
        new_url = new_url.replace("_DutchNaoTeam_", "_Dutch Nao Team_")
        new_url = new_url.replace("_Hulks_", "_HULKs_")
         
        json_obj = {
                    "id": img.id,
                    "image_url": new_url,
                }
        image_data.append(json_obj)

        if idx % 100 == 0 and idx != 0:
            print(idx)
            try:
                response = client.image.bulk_update(data=image_data)
                image_data.clear()
            except Exception as e:
                print(e)
                print("error inputing the data")
                quit()
        

