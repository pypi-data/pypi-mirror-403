# andleeb-drf-auto-crud

**Automatic CRUD API generator for Django models using Django REST Framework (DRF).**

This package simplifies the creation of REST APIs for your Django models. Once installed, it dynamically generates:

- **Serializers** for all your models
- **ViewSets** with complete CRUD operations
- **URL patterns** ready to integrate into Django's `urlpatterns`

The package is designed to be minimal and intuitive. You only need to work with **two modules** in your app:

1. `model.py` – for defining your models
2. `url.py` – for automatically generating URLs for your models

This allows you to spend less time writing repetitive boilerplate and more time focusing on your business logic.

---

## `model.py` – Base Model for Automatic CRUD

The `model.py` module provides a **base model class** that you can extend for all your Django models.

Instead of manually defining database table names and plural verbose names, this base class handles it automatically:

- Converts your model class names to **snake_case table names**
- Automatically generates **plural verbose names** for improved admin readability
- Maintains full compatibility with Django ORM

### Basic Usage

```python
from django.db.models import CharField
from andleeb_drf_auto_crud.model import Model

class MyModel(Model):
    name = CharField(max_length=50, unique=True)
    def __str__(self):
        return self.name
```

---

## `url.py` – Automatic URL Generation for CRUD

The `url.py` module provides a simple way to automatically generate **DRF URL patterns** for all models in your app. It eliminates the need to manually write `ViewSet` routes for each model.

### Key Features

- Automatically registers **ViewSets** for all models in the app
- Provides a **dynamic endpoint** for filtered queries on any model
- Ready to integrate into your Django `urlpatterns` without additional configuration

### Basic Usage

```python
from django.urls import path, include
from andleeb_drf_auto_crud.url import get_drf_auto_urlpatterns
urlpatterns = get_drf_auto_urlpatterns()
```

---

## Installation
```bash
pip install andleeb-drf-auto-crud
```
