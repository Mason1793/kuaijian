from django.shortcuts import render
from django.http import JsonResponse, FileResponse
import json
from fastclip import FastClip, synthetize_Video_Mp3, convert_2_h264
import os
import time
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"


def hello(request):
    context = {}
    context['hello'] = 'Hello Jss!'
    return render(request, 'hello.html', context)


def ckplayer(request):
    return render(request, 'ckplayer.html')


def main(request):
    return render(request, 'main.html')


# 没有心情优化下面两个函数
def add_sound(request):
    print('add_sound')
    sound_obj = request.FILES.get('sound')

    file_path = os.path.join('static', 'sound', sound_obj.name)
    f = open(file_path, 'wb')
    for chunk in sound_obj.chunks():
        f.write(chunk)
    f.close()
    return JsonResponse({"msg": "load success"})


def add_video(request):
    video_obj = request.FILES.get('video')

    file_path = os.path.join('static', 'upload', video_obj.name)
    f = open(file_path, 'wb')
    for chunk in video_obj.chunks():
        f.write(chunk)
    f.close()
    return JsonResponse({"msg":"load success"})


def merge_video(request):
    base_dir = os.getcwd()
    print ("merge_video:"+base_dir)

    data = json.loads(request.body.decode("utf-8"))
    video1 = data.get('video1')
    video2 = data.get('video2')

    file_path1 = os.path.join('static', 'upload', video1)
    file_path2 = os.path.join('static', 'upload', video2)

    time_stamp = str(int(round(time.time() * 1000)))
    output_file = time_stamp + ".mp4"

    sound = data.get('sound')
    if sound != None:
        sound_path = os.path.join('static', 'sound', sound)
    print(file_path1)
    print(file_path2)
    if(sound != None):
        output_path = os.path.join(base_dir, 'static', 'output', 'temp.mp4')
        FastClip(file_path1, file_path2, output_path)
        output_path1 = os.path.join(base_dir, 'static', 'output', output_file)
        synthetize_Video_Mp3(output_path, sound_path, output_path1)
    else:
        output_path = os.path.join(base_dir, 'static', 'output', 'temp.mp4')
        FastClip(file_path1, file_path2, output_path)
        output_path1 = os.path.join(base_dir, 'static', 'output', output_file)
        convert_2_h264(output_path, output_path1)

    return JsonResponse({"msg": "merge success", "output_file": output_file})


def download(request):
    file = request.GET.get(u'file')

    # 文件太大必须分块读取
    def read_file(fn, buf_size=262144):
        f = open(fn, "rb")
        while True:
            c = f.read(buf_size)
            if c:
                yield c
            else:
                break
        f.close()

    file_path = os.path.join('static', 'output', file)
    response = FileResponse(read_file(file_path))
    response['Content-Type'] = 'application/octet-stream'
    response['Content-Disposition'] = 'attachement;filename="{0}"'.format(file)
    return response


