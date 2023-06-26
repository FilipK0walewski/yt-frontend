# Youtube

Very lightweight yutube frontend
[youtube api](https://developers.google.com/youtube/v3/docs)

Features:
- search
- video playback
- playlists

# Installation

```
git clone https://github.com/FilipK0walewski/yt-frontend
cd yt-frontend
pip install -r requirements.txt
export YOUTUBE_API_KEY=your_api_key
uvicorn main:app --reload
```

### using docker

```
git clone https://github.com/FilipK0walewski/yt-frontend
cd yt-frontend
export YOUTUBE_API_KEY=your_api_key
docker compose up
```

open [localhost:8000](http://127.0.0.1:8000) in browser.
