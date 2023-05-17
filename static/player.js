const url = new URL(window.location.href)
const params = new URLSearchParams(url.search)

const videoPlayer = document.getElementById('video-player')
const videoSource = document.getElementById('video-source')
const playlistVideos = document.getElementById('playlist-videos')
const songTitle = document.getElementById('song-title')

const loadingScreen = document.getElementById('loading-screen')
const loadingText = document.getElementById('loading-text')

let n = 0;

const enableLoading = () => {
    loadingScreen.style.display = 'inline'
    loadingText.style.display = 'inline'
}

const disableLoading = () => {
    loadingScreen.style.display = 'none'
    loadingText.style.display = 'none'
}


const setVideo = () => {
    document.documentElement.scrollTop = 0
    videoPlayer.pause()
    videoSource.setAttribute('src', null)

    const videoId = playlistVideos.children[n].getAttribute('value')
    params.set('video', videoId)
    url.search = params.toString();
    window.history.replaceState({}, '', url.href)

    fetch(`${url.origin}/video/${videoId}?raw=true`)
    .then(res => res.json())
    .then(data => {
        videoSource.setAttribute('src', data['url'])
        songTitle.innerText = data['title']
        videoPlayer.load()
        videoPlayer.play()
    })
}

const handleVideoChange = (e) => {
    n = e.target.getAttribute('key') - 1
    setVideo()
}

videoPlayer.addEventListener('ended', () => {
    n += 1
    if (n === playlistVideos.children.length) n = 0
    setVideo()
})

document.querySelectorAll('.playlist-video').forEach(i => {
    i.addEventListener('click', handleVideoChange)
})

document.getElementById('player-btn-prev').addEventListener('click', () => {
    n -= 1
    if (n === -1) n = playlistVideos.children.length - 1
    setVideo()
})

document.getElementById('player-btn-next').addEventListener('click', () => {
    n += 1
    if (n === playlistVideos.children.length) n = 0
    setVideo()
})

window.onload = () => {
    let videoId = params.get('video')
    if (!videoId) {
        videoId = playlistVideos.children[0].getAttribute('value')
    }

    let currentVideo = document.getElementById(videoId)
    if (!currentVideo) {
        videoId = playlistVideos.children[0].getAttribute('value')
        currentVideo = document.getElementById(videoId)
    }

    n = currentVideo.getAttribute('key') - 1
    setVideo()
}
