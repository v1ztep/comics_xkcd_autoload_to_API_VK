import os
import random
from urllib.parse import urljoin

import requests
import urllib3
from dotenv import load_dotenv


def get_response(url, params=None, headers=None):
    response = requests.get(url, params=params, headers=headers, verify=False)
    response.raise_for_status()
    return response


def post_response(url, params=None, headers=None, files=None):
    response = requests.post(url, params=params, headers=headers, verify=False,
                             files=files)
    response.raise_for_status()
    return response


def download_image(url, image_name):
    response = get_response(url)
    with open(image_name, 'wb') as file:
        file.write(response.content)


def get_random_comic_num():
    url = 'https://xkcd.com/info.0.json'
    response = get_response(url)
    comics_details = response.json()
    last_comic = comics_details['num']
    random_comic_num = random.randint(1, last_comic)
    return random_comic_num


def download_random_comic(image_name):
    comic_num = get_random_comic_num()
    url = f'https://xkcd.com/{comic_num}/info.0.json'
    response = get_response(url)
    comic_details = response.json()

    image_url = comic_details['img']
    download_image(image_url, image_name)
    comic_comment = comic_details['alt']
    extra_link = comic_details['link']

    return comic_comment, extra_link


def post_to_vk(vk_access_token, vk_group_id, image_name, comic_comment,
               extra_link):
    actual_version_api = '5.130'
    post_from_group = 1
    base_api_url = 'https://api.vk.com/method/'

    get_upload_url = urljoin(base_api_url, 'photos.getWallUploadServer')
    upload_params = {
        'access_token': vk_access_token,
        'group_id': vk_group_id,
        'v': actual_version_api
    }
    upload_server_response = get_response(get_upload_url, params=upload_params)
    upload_server_details = upload_server_response.json()
    upload_url = upload_server_details['response']['upload_url']

    with open(image_name, 'rb') as file:
        files = {
            'photo': file,
        }
        upload_response = post_response(upload_url, files=files)
        upload_details = upload_response.json()

    save_params = {
        'access_token': vk_access_token,
        'group_id': vk_group_id,
        'v': actual_version_api
    }
    save_params.update(upload_details)
    save_url = urljoin(base_api_url, 'photos.saveWallPhoto')
    save_response = post_response(save_url, params=save_params)
    save_details = save_response.json()

    photo_owner_id = save_details['response'][0]['owner_id']
    image_id = save_details['response'][0]['id']
    attachments = f'photo{photo_owner_id}_{image_id}'
    post_params = {
        'access_token': vk_access_token,
        'v': actual_version_api,
        'owner_id': f'-{vk_group_id}',
        'from_group': post_from_group,
        'attachments': attachments,
        'message': comic_comment
    }
    if extra_link:
        extra_materials = {
            'message': f'{comic_comment}\n\n{extra_link}'
        }
        post_params.update(extra_materials)
    post_url = urljoin(base_api_url, 'wall.post')
    post_response(post_url, params=post_params)


def main():
    load_dotenv()
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    image_name = 'xkcd.png'
    vk_access_token = os.getenv('VK_ACCESS_TOKEN')
    vk_group_id = os.getenv('VK_GROUP_ID')

    comic_comment, extra_link = download_random_comic(image_name)
    post_to_vk(vk_access_token, vk_group_id, image_name, comic_comment,
               extra_link)

    os.remove(image_name)

if __name__ == '__main__':
    main()
