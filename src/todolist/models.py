from django.conf import settings
from django.db import models
from django.urls import reverse


class Item(models.Model):
    text = models.TextField(default='')
    list = models.ForeignKey('List', on_delete=models.CASCADE, default=None)
    done = models.BooleanField(default=False)

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
    shared_with = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name='shared_lists',
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

    def is_owned_by(self, user) -> bool:
        return user.is_authenticated and self.owner_id == user.pk

    def can_be_viewed_by(self, user) -> bool:
        """Lists without an owner are public; owned lists are private to the
        owner and the people the list has been shared with."""
        if self.owner_id is None or self.is_owned_by(user):
            return True
        return user.is_authenticated and self.shared_with.filter(pk=user.pk).exists()
