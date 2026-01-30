import inflect
from django.db.models import Model as DjangoModel
from django.db.models.base import ModelBase
from django.utils.text import camel_case_to_spaces, slugify

p, to_snake = inflect.engine(), lambda n: slugify(camel_case_to_spaces(n)).replace("-", "_")

class MyModelBase(ModelBase):
    def __new__(cls, name, bases, attrs, **kwargs):
        meta = attrs.get("Meta", type("Meta", (), {}))
        if not getattr(meta, "abstract", False):
            if not hasattr(meta, "db_table"): meta.db_table = to_snake(name)
            if not hasattr(meta, "verbose_name_plural"):
                meta.verbose_name_plural = "_".join([*to_snake(name).split("_")[:-1], p.plural(to_snake(name).split("_")[-1])])
        attrs["Meta"] = meta
        return super().__new__(cls, name, bases, attrs, **kwargs)

class Model(DjangoModel, metaclass=MyModelBase):
    class Meta: abstract = True
