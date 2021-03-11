from pathlib import Path

import requests
import urllib3


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
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    images_folder = 'images'
    Path(images_folder).mkdir(parents=True, exist_ok=True)

    comic_number = 353
    url = f'https://xkcd.com/{comic_number}/info.0.json'

    response = get_response(url)
    comic_details = response.json()

    image_url = comic_details['img']
    image_name = comic_details['num']
    download_image(image_url, image_name)
    comic_comment = comic_details['alt']
    print(comic_comment)


if __name__ == '__main__':
    main()
