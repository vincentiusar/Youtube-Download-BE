from django.http import JsonResponse, StreamingHttpResponse, HttpResponse, HttpResponseNotFound
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from pytube import Playlist
import yt_dlp as youtube_dl
import json, time, shutil, os, pathlib, patoolib

def deleteFile() :
    folder = './music'
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.remove(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))

def oldFileDelete(dir, ext) : 
    folder = './'+dir
    now = time.time()
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) and os.stat(file_path).st_mtime < now - 3600 and ext in pathlib.Path(file_path).suffix:
                os.remove(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))

@csrf_exempt
@require_http_methods(['POST'])
def fetch(req):
    oldFileDelete('', '.zip')
    if (not req.body) :
        return JsonResponse({"Status" : 404})

    body_unicode = req.body.decode('utf-8')
    body = json.loads(body_unicode)
    
    if 'url' not in body:
        return JsonResponse({"Status" : 404})

    video_url = body['url']

    video_info = Playlist(video_url)

    info = {
        'playlist title': video_info.title,
        'songs_list': [{'id': id+1, 'title' : item.title, 'thumbnail': item.thumbnail_url, 'webpage_url': video_info[id]} for id, item in enumerate(video_info.videos)],
        'webpage_url': video_info.playlist_url,
    }

    return JsonResponse(info)

def single() :
    return

@csrf_exempt
@require_http_methods(['GET'])
def download(req) :
    if (not req.GET) :
        return JsonResponse({"Status" : 404})

    dir = './' + req.GET.get('id') + '.zip'
    try :
        with open(dir, 'rb') as zip_file:
            file = zip_file.read()
        response = HttpResponse(file, content_type='application/zip')
        response['Content-Disposition'] = 'attachment'
    except IOError:
        response = HttpResponseNotFound('File not exist')
    return response

@csrf_exempt
@require_http_methods(['POST'])
def playlist(req) :
    oldFileDelete('', '.zip')
    if (not req.body) :
        return JsonResponse({"Status" : 404})

    body_unicode = req.body.decode('utf-8')
    body = json.loads(body_unicode)

    for item in body['songs_list']:
        if 'webpage_url' not in item:
            return JsonResponse({"Status" : 404})

    video_info = body['songs_list']

    def progress(d) :
        if d['status'] == 'finished':
            yield (d['playlist_index'])

    prefix = './music/'
    options={
        'format':'bestaudio/best',
        'keepvideo':False,
        'outtmpl': prefix+'/%(title)s.%(ext)s',
        'writethumbnail': True,
        'embedthumbnail': True,
        'quiet': True,
        # 'progress_hooks': [progress],
        'ffmpeg_location': './ffmpeg/bin/ffmpeg.exe',
        'postprocessors': [
            {'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192'},
            {'key': 'EmbedThumbnail',},]
    }

    # For single download
    # filename = f"{prefix}{video_info['title']}"
    
    # For playlist download
    # pprint.pprint(list(video_info['entries'])[0]['fulltitle'])
    # filename = list(video_info['entries'])[i]['fulltitle']

    suff = time.time()
    def download(video_info) :
        i = 1
        with youtube_dl.YoutubeDL(options) as ydl:
            for item in video_info:
                yield f"{i}\n"
                ydl.download(item['webpage_url'])
                i += 1
        yield 'songs_'+str(suff)
        shutil.make_archive('songs_'+str(suff), 'zip', prefix)
        # oldFileDelete('music', '.mp3')
    
    response = StreamingHttpResponse(download(video_info))
    response['content-type'] = 'application/json'

    return response

@csrf_exempt
@require_http_methods(['GET'])
def test(req) :
    def stream():
        for i in range(10):
            yield f"Data {i}\n"
            time.sleep(1)
        yield json.dumps({'playlist title': 'a',
            'songs list': [{'id': 'a', 'title' : 'a', 'thumbnail': 'a'}, {'id': 'a', 'title' : 'a', 'thumbnail': 'a'}]})

    response = StreamingHttpResponse(stream())
    response['content-type'] = 'application/json'
    return response
