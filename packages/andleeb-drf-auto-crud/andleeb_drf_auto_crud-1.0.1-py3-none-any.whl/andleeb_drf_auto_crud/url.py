from django.urls import path
from rest_framework.routers import DefaultRouter
from django.apps import apps
from django.utils.text import camel_case_to_spaces, slugify
from .view import get_generic_viewset, filtered_model_list_view
import inspect

def get_drf_auto_urlpatterns():
    router = DefaultRouter()
    for model in apps.get_app_config(inspect.stack()[1].frame.f_globals.get('__package__')).get_models():
        router.register(slugify(camel_case_to_spaces(model.__name__)), get_generic_viewset(model))
    urlpatterns = [path('dynamic/<str:model_name>/', filtered_model_list_view, name='filtered-model-list')] + router.urls
    return urlpatterns