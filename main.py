import os
import shutil
import requests
from pathlib import Path
from urllib.parse import urlparse
import random
from dotenv import load_dotenv


def download_comic(image_link):
    response = requests.get(image_link)
    response.raise_for_status()
    file_name = os.path.split(urlparse(image_link).path)[1]
    file_path = os.path.join('image', file_name)
    with open(file_path, 'wb') as file:
        file.write(response.content)
    return file_path


def get_last_comic_num():
    current_comic_url = 'https://xkcd.com/info.0.json'
    response = requests.get(current_comic_url)
    response.raise_for_status()
    return response.json()['num']


def get_random_comic():
    current_comic_num = get_last_comic_num()
    random_comic_num = random.randint(1, current_comic_num)
    random_comic_url = f'https://xkcd.com/{random_comic_num}/info.0.json'
    response = requests.get(random_comic_url)
    response.raise_for_status()
    comic_json = response.json()
    message = comic_json['alt']
    file_path = download_comic(comic_json['img'])
    return message, file_path


def get_upload_server(vk_token):
    method = 'photos.getWallUploadServer'
    params = {
        'access_token': vk_token,
        'v': 5.131
    }
    url = f'https://api.vk.com/method/{method}'
    response = requests.get(url, params=params)
    response.raise_for_status()
    server_url = response.json()['response']['upload_url']
    return server_url


def upload_image(file_path, server_url):
    with open(file_path, 'rb') as file:
        files = {'photo': file}
        response = requests.post(server_url, files=files)
    response.raise_for_status()
    uploaded_img_details = response.json()
    server = uploaded_img_details['server']
    photo = uploaded_img_details['photo']
    img_hash = uploaded_img_details['hash']
    return server, photo, img_hash


def save_uploaded_image(vk_token, server, photo, img_hash):
    method = 'photos.saveWallPhoto'
    params = {
        'server': server,
        'photo': photo,
        'hash': img_hash,
        'access_token': vk_token,
        'v': 5.131
    }
    url = f'https://api.vk.com/method/{method}'
    response = requests.post(url, params=params)
    response.raise_for_status()
    wall_image_features = response.json()['response'][0]
    owner_id = wall_image_features['owner_id']
    media_id = wall_image_features['id']
    img_url = wall_image_features['sizes'][-1]['url']
    return owner_id, media_id, img_url


def post_comic_vk(vk_token, group_id, owner_id, media_id, img_url, message):
    method = 'wall.post'
    params = {
        'owner_id': f'-{group_id}',
        'from_group': 1,
        'message': message,
        'attachments': f"photo{owner_id}_{media_id},{img_url}",
        'access_token': vk_token,
        'v': 5.131
    }
    url = f'https://api.vk.com/method/{method}'
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()['response']


def main():
    load_dotenv()
    vk_token = os.environ['VK_ACCESS_TOKEN']
    group_id = os.environ['GROUP_ID']
    Path('image').mkdir(exist_ok=True)
    message, file_path = get_random_comic()
    try:
        server_url = get_upload_server(vk_token)
        server, photo, img_hash = upload_image(file_path, server_url)
        owner_id, media_id, img_url = save_uploaded_image(vk_token, server, photo, img_hash)
        comic_response = post_comic_vk(vk_token, group_id, owner_id, media_id, img_url, message)
        if comic_response['post_id']:
            print('Comic successfully published!')
    finally:
        shutil.rmtree('image', ignore_errors=True)


if __name__ == '__main__':
    main()
