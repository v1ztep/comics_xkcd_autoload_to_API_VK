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


def get_vk_response(url, params=None, headers=None):
    response = requests.get(url, params=params, headers=headers, verify=False)
    response_details = response.json()
    if response_details.get('error'):
        raise requests.HTTPError(response_details['error']['error_msg'])
    return response


def post_vk_response(url, params=None, files=None):
    response = requests.post(url, params=params, files=files, verify=False)
    response_details = response.json()
    if response_details.get('error'):
        raise requests.HTTPError(response_details['error']['error_msg'])
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


def get_upload_url(base_api_url, access_params):
    url = urljoin(base_api_url, 'photos.getWallUploadServer')
    response = get_vk_response(url, params=access_params)
    upload_server_details = response.json()
    upload_url = upload_server_details['response']['upload_url']
    return upload_url


def upload_image(image_name, upload_url):
    with open(image_name, 'rb') as file:
        files = {
            'photo': file,
        }
        upload_response = post_vk_response(upload_url, files=files)
        upload_details = upload_response.json()
        return upload_details


def save_image(base_api_url, access_params, upload_details):
    save_params = {**access_params, **upload_details}
    save_url = urljoin(base_api_url, 'photos.saveWallPhoto')
    save_response = post_vk_response(save_url, params=save_params)
    save_details = save_response.json()
    photo_owner_id = save_details['response'][0]['owner_id']
    image_id = save_details['response'][0]['id']
    return photo_owner_id, image_id


def post_comic(base_api_url, access_params, photo_owner_id, image_id,
               comic_comment, extra_link):
    post_from_group = 1
    post_access = access_params.copy()
    attachments = f'photo{photo_owner_id}_{image_id}'
    post_params = {
        'owner_id': f'-{post_access.pop("group_id")}',
        'from_group': post_from_group,
        'attachments': attachments,
        'message': comic_comment
    }
    post_params.update(post_access)
    if extra_link:
        extra_materials = {
            'message': f'{comic_comment}\n\n{extra_link}'
        }
        post_params.update(extra_materials)

    post_url = urljoin(base_api_url, 'wall.post')
    post_vk_response(post_url, params=post_params)


def main():
    load_dotenv()
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    image_name = 'xkcd.png'
    api_version = '5.130'
    vk_access_token = os.getenv('VK_ACCESS_TOKEN')
    vk_group_id = os.getenv('VK_GROUP_ID')
    base_api_url = 'https://api.vk.com/method/'
    access_params = {
        'access_token': vk_access_token,
        'group_id': vk_group_id,
        'v': api_version
    }

    try:
        comic_comment, extra_link = download_random_comic(image_name)
        upload_url = get_upload_url(base_api_url, access_params)
        upload_details = upload_image(image_name, upload_url)
        photo_owner_id, image_id = \
            save_image(base_api_url, access_params, upload_details)
        post_comic(base_api_url, access_params, photo_owner_id, image_id,
                   comic_comment, extra_link)
    except requests.HTTPError as err:
        print(f'Ошибка: {err}')
    finally:
        os.remove(image_name)


if __name__ == '__main__':
    main()
