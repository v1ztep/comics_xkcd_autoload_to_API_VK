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

    # 'https://xkcd.com/404/info.0.json' убрать 404, 1608, 1663 из выборки = мёртвые
    # https://xkcd.com/1127/info.0.json есть варианты с большим размером large

    comic_number = 2399
    url = f'https://xkcd.com/{comic_number}/info.0.json'

    response = get_response(url)
    comic_details = response.json()

    image_url = comic_details['img']
    image_name = comic_details['num']
    download_image(image_url, image_name, images_folder=images_folder)
    comic_comment = comic_details['alt']
############################# Удалить??? #############################
    image_link = comic_details['link']
###################### Получение адреса на загрузку фото #####################

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

###################### Загрузка на сервер ВК ################################
    image_path = Path(f'{images_folder}/{image_name}.png')

    with open(image_path, 'rb') as file:
        files = {
            'photo': file,
        }
        response = requests.post(upload_url, files=files)
        response.raise_for_status()
        vk_details = response.json()
        print(vk_details)

###################### Сохранение в альбом ВК ###############################
    method_name = 'photos.saveWallPhoto'
    save_url = f'https://api.vk.com/method/{method_name}'

    params.update(vk_details)

    response = requests.post(save_url, params=params)
    response.raise_for_status()

    vk_details = response.json()
    with open("description.json", "w", encoding='utf8') as file:
        json.dump(vk_details, file, ensure_ascii=False, indent=4)

##################### Пост на стене ВК группы ###############################
    photo_owner_id = vk_details['response'][0]['owner_id']
    image_id = vk_details['response'][0]['id']

    post_from_group = 1
    attachments = f'photo{photo_owner_id}_{image_id}'


    params = {
        'access_token': vk_access_token,
        'v': actual_version_api,
        'owner_id': f'-{vk_group_id}',
        'from_group': post_from_group,
        'attachments': attachments,
        'message': comic_comment
    }
    if image_link:
        additional_materials = {'message': f'{comic_comment}\n\n{image_link}'}
        params.update(additional_materials)


    method_name = 'wall.post'
    post_url = f'https://api.vk.com/method/{method_name}'
    response = requests.post(post_url, params=params)
    response.raise_for_status()

    vk_details = response.json()


    with open("description.json", "w", encoding='utf8') as file:
        json.dump(vk_details, file, ensure_ascii=False, indent=4)


if __name__ == '__main__':
    main()
