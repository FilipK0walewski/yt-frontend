import aiohttp
import aioredis
import json
import os
import pytube

from fastapi import FastAPI, Form, Request
from fastapi.exceptions import HTTPException
from fastapi.responses import HTMLResponse, FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

rc, session = None, None
API_KEY = os.environ.get('YOUTUBE_API_KEY')

app = FastAPI()


@app.on_event('startup')
async def app_startup():
    global rc, session
    redis_host = os.environ.get('REDIS_HOST', 'localhost')
    redis_port = os.environ.get('REDIS_PORT', 6379)
    rc = aioredis.from_url(f'redis://{redis_host}:{redis_port}', decode_responses=True)
    session = aiohttp.ClientSession(headers={'Accept': 'application/json'})


@app.on_event('shutdown')
async def app_shutodwn():
    await rc.close()
    await session.close()


app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/")
async def main(request: Request):
    key = 'youtube.search.default'
    cahced = await rc.get(key)
    if cahced is not None:
        cahced = json.loads(cahced)
        return templates.TemplateResponse('index.html', {'request': request, 'items': cahced['items']})

    print(API_KEY)
    params = {'part': 'snippet', 'maxResults': 18, 'key': API_KEY, 'countryCode': 'PL'}
    async with session.get('https://youtube.googleapis.com/youtube/v3/search', params=params) as r:
        if r.status != 200:
            return templates.TemplateResponse('index.html', {'request': request})
        res_json = await r.json()

    await rc.setex(key, 3600, json.dumps(res_json))
    return templates.TemplateResponse('index.html', {'request': request, 'items': res_json['items']})


@app.get('/search')
async def search(request: Request, q: str | None = None):
    key = f'youtube.search.{q}'
    cached = await rc.get(key)
    if cached is not None:
        cached = json.loads(cached)
        return templates.TemplateResponse('index.html', {'request': request, 'items': cached['items'], 'q': q})

    params = {'part': 'snippet', 'q': q, 'maxResults': 18, 'key': API_KEY, 'countryCode': 'PL'}
    async with session.get(f'https://youtube.googleapis.com/youtube/v3/search', params=params) as r:
        if r.status != 200:
            return templates.TemplateResponse('index.html', {'request': request})
        res_json = await r.json()

    rc.setex(key, 3600, json.dumps(res_json))
    return templates.TemplateResponse('index.html', {'request': request, 'items': res_json['items'], 'q': q})


@app.get('/video/{video_id}')
async def get_video(request: Request, video_id: str , raw: bool | None = None):
    key = f'youtube.video.{video_id}'
    cached = await rc.get(key)
    if cached is not None:
        cached = json.loads(cached)
        if raw is True:
            return cached
        return templates.TemplateResponse('video.html', {'request': request, 'data': cached})

    data = {}
    params = {'part': 'snippet', 'id': video_id, 'key': API_KEY}
    async with session.get('https://www.googleapis.com/youtube/v3/videos', params=params) as r:
        res_json = await r.json()
        items = res_json['items']
        if len(items) == 0:
            return None

        video = items[0]['snippet']
        data['title'] = video['title']

        yt = pytube.YouTube(f'https://www.youtube.com/watch?v={video_id}')
        stream = yt.streams.get_highest_resolution()
        data['url'] = stream.url

        await rc.setex(key, 14399, json.dumps(data))
        if raw is True:
            return data
        return templates.TemplateResponse('video.html', {'request': request, 'data': data})


@app.get('/playlist/{playlist_id}')
async def get_playlist(request: Request, playlist_id: str):
    key = f'youtube.playlist.{playlist_id}'
    cached = await rc.get(key)
    if cached is not None:
        return templates.TemplateResponse('playlist.html', {'request': request, 'data': json.loads(cached)})

    data = {'videos': []}
    params = {'part': 'snippet', 'id': playlist_id, 'key': API_KEY}
    async with session.get('https://www.googleapis.com/youtube/v3/playlists', params=params) as r:
        playlist_data = await r.json()

    data['title'] = playlist_data['items'][0]['snippet']['title']
    params = {'part': 'snippet', 'playlistId': playlist_id, 'maxResults': 50, 'key': API_KEY}
    async with session.get('https://www.googleapis.com/youtube/v3/playlistItems', params=params) as r:
        playlist_items = await r.json()

    for item in playlist_items['items']:
        video = {
            'title': item['snippet']['title'], 
            'thumbnail': item['snippet']['thumbnails']['default']['url'] if item['snippet']['thumbnails'] else None, 
            'id': item['snippet']['resourceId']['videoId']
        }
        data['videos'].append(video)

    await rc.setex(key, 14399, json.dumps(data))
    return templates.TemplateResponse('playlist.html', {'request': request, 'data': data})


@app.get('/channel/{channel_id}')
async def get_channel(request: Request, channel_id: str):
    return templates.TemplateResponse('channel.html', {'request': request})


@app.exception_handler(404)
async def not_found(request: Request, exc: HTTPException):
    return templates.TemplateResponse("404.html", {"request": request}, status_code=404)
