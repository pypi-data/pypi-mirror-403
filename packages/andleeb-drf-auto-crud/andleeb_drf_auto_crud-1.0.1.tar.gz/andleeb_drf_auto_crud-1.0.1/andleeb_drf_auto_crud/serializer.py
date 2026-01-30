from rest_framework.serializers import ModelSerializer
from django.db.models import ForeignKey, ManyToManyField
def get_auto_serializer(model_class):
    fields=[f for f in model_class._meta.get_fields() if not (f.auto_created and not f.concrete)]
    names=[f.name for f in fields]; cache={}
    
    class Serializer(ModelSerializer):
        def to_representation(self, instance):
            visited=getattr(self,"_visited",set())
            def nested(obj):
                if (k:=(obj.__class__,obj.pk)) in visited: return obj.pk
                visited.add(k)
                return cache.setdefault(obj.__class__,
                    type(f'{obj.__class__.__name__}Nested',(ModelSerializer,),
                    {'Meta':type('Meta',(),{'model':obj.__class__,'fields':names})})
                )(obj).data
            return {f.name:
                nested(v) if isinstance(f,ForeignKey) and (v:=getattr(instance,f.name))
                else [nested(o) for o in getattr(instance,f.name).all()] if isinstance(f,ManyToManyField)
                else getattr(instance,f.name) for f in fields}
        class Meta: model=model_class; fields='__all__'
    return Serializer
