# Copyright 2026 EcoFuture Technology Services LLC and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from django.conf import settings
from django.contrib.gis.db import models

from bazis.contrib.users.models_abstract import UserMixin


class AuthorMixin(UserMixin):
    """
    Mixin that enables working with author fields in a model
    """

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='author_%(class)s',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    author_updated = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='author_updated_%(class)s',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if author := self.CTX_USER_REQUEST.get():
            if not self.author:
                self.author = author
            self.author_updated = author
        super().save(*args, **kwargs)
