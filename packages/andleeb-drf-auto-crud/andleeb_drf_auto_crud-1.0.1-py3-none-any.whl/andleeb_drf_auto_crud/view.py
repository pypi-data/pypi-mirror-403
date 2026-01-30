from rest_framework.viewsets import ModelViewSet
from .serializer import get_auto_serializer
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.apps import apps
from django.http import Http404
from django.db.models import ForeignKey, ManyToManyField

def get_generic_viewset(model_class):
    fk_fields = [f.name for f in model_class._meta.fields if isinstance(f, ForeignKey)]
    m2m_fields = [f.name for f in model_class._meta.get_fields() if isinstance(f, ManyToManyField)]
    class GenericViewSet(ModelViewSet):
        queryset = model_class.objects.select_related(*fk_fields).prefetch_related(*m2m_fields)
        serializer_class = get_auto_serializer(model_class)
    return GenericViewSet

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def filtered_model_list_view(request, model_name):
    if not (model := apps.get_model('api', ''.join(w.capitalize() for w in model_name.split('-')))): raise Http404()
    filters, nested = {}, False
    for k, v in request.query_params.items():
        nested = nested or '__' in k
        filters[k if '__' in k or (k in model._meta.get_fields() and not isinstance(model._meta.get_field(k), ForeignKey)) 
            else f'{k[:-3]}__id'] = v
    qs = model.objects.filter(**filters)
    return Response(get_auto_serializer(model)((qs.distinct() if nested else qs), many=True).data)
