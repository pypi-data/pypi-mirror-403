# Bazis Author

[![PyPI version](https://img.shields.io/pypi/v/bazis-author.svg)](https://pypi.org/project/bazis-author/)
[![Python Versions](https://img.shields.io/pypi/pyversions/bazis-author.svg)](https://pypi.org/project/bazis-author/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

An extension package for Bazis that provides automatic authorship tracking for models (who created and who updated records).

## Quick Start

```bash
# Install the package
uv add bazis-author

# Create model with authorship tracking
from bazis.contrib.author.models_abstract import AuthorMixin
from bazis.core.models_abstract import DtMixin, UuidMixin, JsonApiMixin
from django.db import models

class Article(AuthorMixin, DtMixin, UuidMixin, JsonApiMixin):
    """Article with author tracking"""
    title = models.CharField(max_length=255)
    content = models.TextField()
    
    class Meta:
        verbose_name = 'Article'
        verbose_name_plural = 'Articles'

# Create route with automatic author population
from bazis.contrib.author.routes_abstract import AuthorRouteBase
from django.apps import apps

class ArticleRouteSet(AuthorRouteBase):
    model = apps.get_model('myapp.Article')
```

## Table of Contents

- [Description](#description)
- [Requirements](#requirements)
- [Installation](#installation)
- [Core Components](#core-components)
  - [Model Mixins](#model-mixins)
  - [Base Routes](#base-routes)
  - [Admin Mixins](#admin-mixins)
- [Usage](#usage)
  - [Creating Model with Authorship](#creating-model-with-authorship)
  - [Creating Route with Authorship](#creating-route-with-authorship)
  - [Admin Setup](#admin-setup)
- [How It Works](#how-it-works)
- [Examples](#examples)
- [License](#license)
- [Links](#links)

## Description

**Bazis Author** is an extension package for the Bazis framework that provides automatic authorship tracking for records. The package includes:

- **AuthorMixin** — mixin for models adding `author` (who created) and `author_updated` (who updated) fields
- **AuthorRouteBase** and **AuthorRequiredRouteBase** — base route classes with automatic author field population
- **AuthorAdminMixin** — admin mixin with convenient filters and readonly fields

The main advantage of the package is fully automatic author field population without the need to write additional code.

**This package requires `bazis` and `bazis-users` packages to be installed.**

## Requirements

- **Python**: 3.12+
- **bazis**: latest version
- **bazis-users**: latest version
- **PostgreSQL**: 12+
- **Redis**: For caching

## Installation

### Using uv (recommended)

```bash
uv add bazis-author
```

### Using pip

```bash
pip install bazis-author
```

## Core Components

### Model Mixins

#### AuthorMixin

Mixin for models adding authorship tracking fields.

**Location**: `bazis.contrib.author.models_abstract.AuthorMixin`

**Added fields**:

- `author` — Foreign Key to user who created the record (nullable)
- `author_updated` — Foreign Key to user who last updated the record (nullable)

**Features**:

- Inherits from `UserMixin`, has access to user context via `CTX_USER_REQUEST`
- Automatically populates `author` when creating record
- Automatically updates `author_updated` on every save
- Fields are optional (nullable), so records can be created without a user

**Example usage**:

```python
from bazis.contrib.author.models_abstract import AuthorMixin
from bazis.core.models_abstract import DtMixin, UuidMixin, JsonApiMixin
from django.db import models

class Document(AuthorMixin, DtMixin, UuidMixin, JsonApiMixin):
    """Document with authorship tracking"""
    title = models.CharField('Title', max_length=255)
    content = models.TextField('Content')
    
    class Meta:
        verbose_name = 'Document'
        verbose_name_plural = 'Documents'
```

### Base Routes

#### AuthorRouteMixin

Base mixin for routes that automatically populate author fields.

**Location**: `bazis.contrib.author.routes_abstract.AuthorRouteMixin`

**Features**:

- Excludes `author` and `author_updated` fields from CREATE and UPDATE schemas (they are populated automatically)
- Uses `hook_before_create` and `hook_before_update` hooks to set author
- Sets author only for authenticated users

**Methods**:

- `hook_before_create(item)` — sets `author` before creating record
- `hook_before_update(item)` — sets `author_updated` before updating record

#### AuthorRouteBase

Base route class with authorship support for optional authentication.

**Location**: `bazis.contrib.author.routes_abstract.AuthorRouteBase`

**Inheritance**: `AuthorRouteMixin` + `UserRouteBase`

Use this class when endpoints are accessible to both authenticated and anonymous users.

**Example usage**:

```python
from bazis.contrib.author.routes_abstract import AuthorRouteBase
from django.apps import apps

class ArticleRouteSet(AuthorRouteBase):
    """Route for articles with automatic authorship"""
    model = apps.get_model('myapp.Article')
```

#### AuthorRequiredRouteBase

Base route class with authorship support for required authentication.

**Location**: `bazis.contrib.author.routes_abstract.AuthorRequiredRouteBase`

**Inheritance**: `AuthorRouteMixin` + `UserRequiredRouteBase`

Use this class when endpoints require mandatory authentication (return 401 for unauthenticated requests).

**Example usage**:

```python
from bazis.contrib.author.routes_abstract import AuthorRequiredRouteBase
from django.apps import apps

class PrivateDocumentRouteSet(AuthorRequiredRouteBase):
    """Route for private documents (authenticated only)"""
    model = apps.get_model('myapp.PrivateDocument')
```

### Admin Mixins

#### AuthorAdminMixin

Mixin for Django admin classes adding convenient work with author fields.

**Location**: `bazis.contrib.author.admin_abstract.AuthorAdminMixin`

**Capabilities**:

- Adds `author__username` to search fields
- Makes `author` and `author_updated` fields readonly
- Adds autocomplete filter by author to list view
- Automatically populates author fields when saving through admin

**Example usage**:

```python
from django.contrib import admin
from bazis.contrib.author.admin_abstract import AuthorAdminMixin
from bazis.core.admin_abstract import DtAdminMixin
from .models import Article

@admin.register(Article)
class ArticleAdmin(AuthorAdminMixin, DtAdminMixin, admin.ModelAdmin):
    list_display = ('id', 'title', 'author', 'author_updated', 'dt_created')
    search_fields = ('title', 'content')
```

## Usage

### Creating Model with Authorship

```python
from bazis.contrib.author.models_abstract import AuthorMixin
from bazis.core.models_abstract import DtMixin, UuidMixin, JsonApiMixin
from django.db import models

class Article(AuthorMixin, DtMixin, UuidMixin, JsonApiMixin):
    """Article with automatic author tracking"""
    title = models.CharField('Title', max_length=255)
    content = models.TextField('Content')
    is_published = models.BooleanField('Published', default=False)
    
    class Meta:
        verbose_name = 'Article'
        verbose_name_plural = 'Articles'
    
    def __str__(self):
        return self.title
```

### Creating Route with Authorship

#### For public endpoints (optional authentication)

```python
from bazis.contrib.author.routes_abstract import AuthorRouteBase
from django.apps import apps

class ArticleRouteSet(AuthorRouteBase):
    """
    Articles can be created by anonymous users.
    If user is authenticated - author fields will be populated automatically.
    """
    model = apps.get_model('myapp.Article')
```

**Behavior**:
- Anonymous user creates record → `author` and `author_updated` remain `null`
- Authenticated user creates record → `author` is automatically populated
- Any user updates record → `author_updated` is populated if user is authenticated

#### For private endpoints (required authentication)

```python
from bazis.contrib.author.routes_abstract import AuthorRequiredRouteBase
from django.apps import apps

class PrivateDocumentRouteSet(AuthorRequiredRouteBase):
    """
    Documents are accessible only to authenticated users.
    Anonymous users will get 401.
    """
    model = apps.get_model('myapp.PrivateDocument')
```

**Behavior**:
- Anonymous user tries to create/update record → 401 Unauthorized
- Authenticated user creates record → `author` is automatically populated
- Authenticated user updates record → `author_updated` is automatically updated

### Admin Setup

```python
from django.contrib import admin
from bazis.contrib.author.admin_abstract import AuthorAdminMixin
from bazis.core.admin_abstract import DtAdminMixin
from .models import Article

@admin.register(Article)
class ArticleAdmin(AuthorAdminMixin, DtAdminMixin, admin.ModelAdmin):
    list_display = ('id', 'title', 'author', 'author_updated', 'is_published', 'dt_created')
    search_fields = ('title', 'content')
    list_filter = ('is_published',)
    readonly_fields = ('dt_created', 'dt_updated')
```

**What AuthorAdminMixin provides**:

1. **Autocomplete filter by author** in list view
2. **Search by author username** (`author__username`)
3. **Readonly fields** `author` and `author_updated` (cannot be edited)
4. **Automatic population** when saving through admin

## How It Works

### In Models

When calling `save()` on a model with `AuthorMixin`:

1. Check for user presence in `CTX_USER_REQUEST` context
2. If user exists:
   - When creating record (`author` is empty) → set `author`
   - When updating record → update `author_updated`
3. Call `super().save()` to save

```python
def save(self, *args, **kwargs):
    if author := self.CTX_USER_REQUEST.get():
        if not self.author:
            self.author = author
        self.author_updated = author
    super().save(*args, **kwargs)
```

### In Routes

When creating/updating record via API:

1. **In CREATE**: `hook_before_create(item)` is triggered
   - If user is NOT anonymous → set `item.author`
   
2. **In UPDATE**: `hook_before_update(item)` is triggered
   - If user is NOT anonymous → set `item.author_updated`

3. Fields `author` and `author_updated` are **excluded** from CREATE/UPDATE schemas, so client cannot pass them

```python
fields: dict[ApiAction, SchemaFields] = {
    CrudApiAction.CREATE: SchemaFields(
        exclude={'author': None, 'author_updated': None},
    ),
    CrudApiAction.UPDATE: SchemaFields(
        exclude={'author': None, 'author_updated': None},
    ),
}
```

### In Admin

When saving through Django Admin:

1. `save_model()` — sets author from `request.user`
2. `save_formset()` — sets author for inline models

## Examples

### Complete Application Example

**models.py**:
```python
from bazis.contrib.author.models_abstract import AuthorMixin
from bazis.core.models_abstract import DtMixin, UuidMixin, JsonApiMixin
from django.db import models

class Article(AuthorMixin, DtMixin, UuidMixin, JsonApiMixin):
    """Public article"""
    title = models.CharField('Title', max_length=255)
    content = models.TextField('Content')
    is_published = models.BooleanField('Published', default=False)
    
    class Meta:
        verbose_name = 'Article'
        verbose_name_plural = 'Articles'

class PrivateNote(AuthorMixin, DtMixin, UuidMixin, JsonApiMixin):
    """Private note (authenticated only)"""
    title = models.CharField('Title', max_length=255)
    content = models.TextField('Content')
    
    class Meta:
        verbose_name = 'Note'
        verbose_name_plural = 'Notes'
```

**routes.py**:
```python
from bazis.contrib.author.routes_abstract import AuthorRouteBase, AuthorRequiredRouteBase
from django.apps import apps

class ArticleRouteSet(AuthorRouteBase):
    """Articles accessible to everyone, but author is tracked if user is authenticated"""
    model = apps.get_model('myapp.Article')

class PrivateNoteRouteSet(AuthorRequiredRouteBase):
    """Notes accessible only to authenticated users"""
    model = apps.get_model('myapp.PrivateNote')
```

**router.py**:
```python
from bazis.core.routing import BazisRouter
from . import routes

router = BazisRouter(tags=['Content'])
router.register(routes.ArticleRouteSet.as_router())
router.register(routes.PrivateNoteRouteSet.as_router())
```

**admin.py**:
```python
from django.contrib import admin
from bazis.contrib.author.admin_abstract import AuthorAdminMixin
from bazis.core.admin_abstract import DtAdminMixin
from .models import Article, PrivateNote

@admin.register(Article)
class ArticleAdmin(AuthorAdminMixin, DtAdminMixin, admin.ModelAdmin):
    list_display = ('id', 'title', 'author', 'is_published', 'dt_created')
    search_fields = ('title', 'content')
    list_filter = ('is_published',)

@admin.register(PrivateNote)
class PrivateNoteAdmin(AuthorAdminMixin, DtAdminMixin, admin.ModelAdmin):
    list_display = ('id', 'title', 'author', 'dt_created')
    search_fields = ('title', 'content')
```

### API Usage Examples

**Creating article by anonymous user**:
```bash
POST /api/v1/content/article/
Content-Type: application/json

{
  "data": {
    "type": "myapp.article",
    "attributes": {
      "title": "My Article",
      "content": "Article content",
      "is_published": true
    }
  }
}

# Response: 201 Created
# author and author_updated will be null
```

**Creating article by authenticated user**:
```bash
POST /api/v1/content/article/
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "data": {
    "type": "myapp.article",
    "attributes": {
      "title": "My Article",
      "content": "Article content",
      "is_published": true
    }
  }
}

# Response: 201 Created
# author is automatically set to current user
```

**Attempting to create private note without authentication**:
```bash
POST /api/v1/content/private_note/
Content-Type: application/json

{
  "data": {
    "type": "myapp.privatenote",
    "attributes": {
      "title": "Secret Note",
      "content": "Secret content"
    }
  }
}

# Response: 401 Unauthorized
```

**Creating private note with authentication**:
```bash
POST /api/v1/content/private_note/
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "data": {
    "type": "myapp.privatenote",
    "attributes": {
      "title": "Secret Note",
      "content": "Secret content"
    }
  }
}

# Response: 201 Created
# author is automatically set to current user
```

### Authorship Check in Responses

Fields `author` and `author_updated` are returned in the `relationships` block:

```json
{
  "data": {
    "type": "myapp.article",
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "attributes": {
      "title": "My Article",
      "content": "Article content",
      "is_published": true
    },
    "relationships": {
      "author": {
        "data": {
          "type": "users.user",
          "id": "456e7890-e89b-12d3-a456-426614174000"
        }
      },
      "author_updated": {
        "data": {
          "type": "users.user",
          "id": "456e7890-e89b-12d3-a456-426614174000"
        }
      }
    }
  }
}
```

## License

Apache License 2.0

See [LICENSE](LICENSE) file for details.

## Links

- [Bazis Documentation](https://github.com/ecofuture-tech/bazis) — main repository
- [Bazis Users](https://github.com/ecofuture-tech/bazis-users) — user management package
- [Bazis Author Repository](https://github.com/ecofuture-tech/bazis-author) — package repository
- [Issue Tracker](https://github.com/ecofuture-tech/bazis-author/issues) — report bugs or request features

## Support

If you have questions or issues:
- Check the [Bazis documentation](https://github.com/ecofuture-tech/bazis)
- Search [existing issues](https://github.com/ecofuture-tech/bazis-author/issues)
- Create a [new issue](https://github.com/ecofuture-tech/bazis-author/issues/new) with detailed information

---

Made with ❤️ by the Bazis team