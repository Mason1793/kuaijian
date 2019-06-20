"""kuaijian URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin
from django.conf.urls import url
from . import view
urlpatterns = [
    url('hello/', view.hello),
    url('main', view.main),
    url('add_video', view.add_video),
    url('add_sound', view.add_sound),
    url('merge_video', view.merge_video),
    url('download', view.download),
    url('query_finished_tag', view.query_finished_tag),
    url('ckplayer', view.ckplayer),
    url('^$', view.main),
]
