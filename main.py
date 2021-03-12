import json
import os
from pathlib import Path

import requests
import urllib3
from dotenv import load_dotenv


def get_response(url, params=None, headers=None):
    response = requests.get(url, params=params, headers=headers, verify=False)
    response.raise_for_status()
    return response


def download_image(url, image_name, images_folder='images'):
    response = get_response(url)

    image_path = Path(f'{images_folder}/{image_name}.png')
    with open(image_path, 'wb') as file:
        file.write(response.content)


def main():
    load_dotenv()
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    images_folder = 'images'
    vk_access_token = os.getenv('VK_ACCESS_TOKEN')
    vk_group_id = os.getenv('VK_GROUP_ID')

    Path(images_folder).mkdir(parents=True, exist_ok=True)

    comic_number = 353
    url = f'https://xkcd.com/{comic_number}/info.0.json'

    response = get_response(url)
    comic_details = response.json()

    image_url = comic_details['img']
    image_name = comic_details['num']
    download_image(image_url, image_name, images_folder=images_folder)
    comic_comment = comic_details['alt']

    actual_version_api = '5.130'


    method_name = 'photos.getWallUploadServer'
    url = f'https://api.vk.com/method/{method_name}'

    params = {
        'access_token': vk_access_token,
        'group_id': vk_group_id,
        'v': actual_version_api
    }

    response = get_response(url, params=params)
    vk_details = response.json()
    print(vk_details)

    upload_url = vk_details['response']['upload_url']


    image_path = Path(f'{images_folder}/{image_name}.png')

    with open(image_path, 'rb') as file:
        files = {
            'photo': file,
        }
        response = requests.post(upload_url, files=files)
        response.raise_for_status()
        vk_details = response.json()


    with open("description.json", "w", encoding='utf8') as file:
        json.dump(vk_details, file, ensure_ascii=False, indent=4)


if __name__ == '__main__':
    main()
