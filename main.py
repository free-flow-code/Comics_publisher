import os
import requests
from pathlib import Path
from urllib.parse import urlparse
import random
from dotenv import load_dotenv


def download_comic(image_link):
    response = requests.get(image_link)
    response.raise_for_status()
    file_name = os.path.split(urlparse(image_link).path)[1]
    file_path = 'image/{}'.format(file_name)
    with open(file_path, 'wb') as file:
        file.write(response.content)
    return file_path


def get_last_comic_num():
    current_comic_url = 'https://xkcd.com/info.0.json'
    response = requests.get(current_comic_url)
    response.raise_for_status()
    return response.json()['num']


def get_random_comic():
    comic_features = {}
    current_comic_num = get_last_comic_num()
    random_comic_num = random.randint(1, current_comic_num)
    random_comic_url = f'https://xkcd.com/{random_comic_num}/info.0.json'
    response = requests.get(random_comic_url)
    response.raise_for_status()
    comic_json = response.json()
    comic_features['message'] = comic_json['alt']
    comic_features['file_path'] = download_comic(comic_json['img'])
    return comic_features


def get_upload_server(vk_token):
    method = 'photos.getWallUploadServer'
    params = {
        'access_token': vk_token,
        'v': 5.131
    }
    url = f'https://api.vk.com/method/{method}'
    response = requests.get(url, params=params)
    response.raise_for_status()
    upload_url = response.json()['response']['upload_url']
    return upload_url


def upload_image(vk_token, file_path):
    upload_url = get_upload_server(vk_token)
    with open(file_path, 'rb') as file:
        files = {'photo': file}
        response = requests.post(upload_url, files=files)
        response.raise_for_status()
    uploaded_image_json = response.json()
    server = uploaded_image_json['server']
    photo = uploaded_image_json['photo']
    hash = uploaded_image_json['hash']
    return server, photo, hash


def save_uploaded_image(vk_token, random_comic):
    method = 'photos.saveWallPhoto'
    server, photo, hash = upload_image(vk_token, random_comic['file_path'])
    params = {
        'server': server,
        'photo': photo,
        'hash': hash,
        'access_token': vk_token,
        'v': 5.131
    }
    url = f'https://api.vk.com/method/{method}'
    response = requests.post(url, params=params)
    response.raise_for_status()
    return response.json()['response'][0]


def post_comic_vk(vk_token, group_id, random_comic):
    method = 'wall.post'
    upload_image_features = save_uploaded_image(vk_token, random_comic)
    print(upload_image_features)
    img_owner_id = upload_image_features['owner_id']
    img_media_id = upload_image_features['id']
    img_urls = upload_image_features['sizes']
    params = {
        'owner_id': f'-{group_id}',
        'from_group': 1,
        'message': random_comic['message'],
        'attachments': f"photo{img_owner_id}_{img_media_id},{img_urls[-1]['url']}",
        'access_token': vk_token,
        'v': 5.131
    }
    url = f'https://api.vk.com/method/{method}'
    response = requests.get(url, params=params)
    response.raise_for_status()
    if response.json()['response']['post_id']:
        print('Comic successfully published!')


def main():
    vk_token = os.environ['VK_ACCESS_TOKEN']
    group_id = os.environ['GROUP_ID']
    Path('./image').mkdir(exist_ok=True)
    random_comic = get_random_comic()
    post_comic_vk(vk_token, group_id, random_comic)
    os.remove(random_comic['file_path'])
    os.rmdir('./image')


if __name__ == '__main__':
    load_dotenv()
    main()
