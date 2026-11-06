from django.conf import settings
from django.db import models
from django.urls import reverse


class Item(models.Model):
    text = models.TextField(default='')
    list = models.ForeignKey('List', on_delete=models.RESTRICT, default=None)

    class Meta:
        ordering = ('id',)
        unique_together = ('list', 'text')

    def __str__(self) -> str:
        return self.text


class List(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lists',
    )

    def __str__(self) -> str:
        return self.name

    def get_absolute_url(self):
        return reverse('todolist:view_list', args=[self.id])

    @property
    def name(self) -> str:
        """A list is named after its first item."""
        first_item = self.item_set.first()
        return first_item.text if first_item else f'List {self.pk}'
