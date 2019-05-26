from django.shortcuts import render
from django.http import JsonResponse
import json
from fastclip import FastClip
import os


def hello(request):
    context = {}
    context['hello'] = 'Hello Jss!'
    return render(request, 'hello.html', context)


def main(request):
    return render(request, 'main.html')


def add_video(request):
    print ("add_video")
    video_obj = request.FILES.get('video')

    file_path = os.path.join('static', 'upload', video_obj.name)
    f = open(file_path, 'wb')
    for chunk in video_obj.chunks():
        f.write(chunk)
    f.close()

    return JsonResponse({"msg":"load success"})


def merge_video(request):
    print ("merge_video")
    data = json.loads(request.body.decode("utf-8"))
    video1 = data.get('video1')
    video2 = data.get('video2')
    print (video1)
    print (video2)
    file_path1 = os.path.join('static', 'upload', video1)
    file_path2 = os.path.join('static', 'upload', video2)

    output_path = os.path.join('static', 'output')
    FastClip(file_path1, file_path2, output_path)

    return JsonResponse({"msg":"load success"})
