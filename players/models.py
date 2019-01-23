import uuid

from django.contrib.postgres.fields import JSONField
from django.db import models


class Player(models.Model):
    uid = models.CharField(max_length=100, unique=True, db_index=True, null=True, blank=True)
    username = models.CharField(max_length=50, unique=True)
    platforms = models.ManyToManyField('core.Platform', related_name='players', blank=True)
    seasons = models.ManyToManyField('core.Season', related_name='players', blank=True)
    friend = models.BooleanField(default=False)

    date_added = models.DateTimeField(auto_now_add=True)
    date_changed = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.username}'

    @property
    def clean_uid(self):
        if self.uid:
            return self.uid.replace('-', '')

    def last_platform(self):
        return self.statuses.last().platform

    def last_platform_name(self):
        return self.last_platform().name

    def status(self):
        return self.statuses.last()


class PlayerStats(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    player = models.ForeignKey(
        'players.Player', related_name='statuses', on_delete=models.CASCADE,
    )
    platform = models.ForeignKey(
        'core.Platform', related_name='statuses', on_delete=models.CASCADE, blank=True,
    )
    data = JSONField(null=True, blank=True)
    stats_solo = JSONField(null=True, blank=True)
    stats_duo = JSONField(null=True, blank=True)
    stats_squad = JSONField(null=True, blank=True)
    stats_lifetime = JSONField(null=True, blank=True)
    recent_matches = JSONField(null=True, blank=True)

    date_added = models.DateTimeField(auto_now_add=True, db_index=True)
    date_changed = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Status # {self.id} - {self.player.username}'

    class Meta:
        verbose_name_plural = 'player statuses'
        ordering = ('date_added',)

    def save(self, *args, **kwargs):
        if not self.data.get('error'):
            if not self.stats_solo:
                self.stats_solo = self.data['stats'].get('p2')
            if not self.stats_duo:
                self.stats_duo = self.data['stats'].get('p10')
            if not self.stats_squad:
                self.stats_squad = self.data['stats'].get('p9')
            if not self.stats_lifetime:
                self.stats_lifetime = self.data['lifeTimeStats']
            if not self.recent_matches:
                self.recent_matches = self.data['recentMatches']

        if window_name and not error:
            if not self.window:
                window, _ = Season.objects.get_or_create(name=window_name)
                self.window = window
            if not self.stats_solo:
                self.stats_solo = {
                    k: v for k, v in self.data['stats'].items() if isinstance(k, str) and k.endswith('_solo')
                }
            if not self.stats_duo:
                self.stats_duo = {
                    k: v for k, v in self.data['stats'].items() if isinstance(k, str) and k.endswith('_duo')
                }
            if not self.stats_squad:
                self.stats_squad = {
                    k: v for k, v in self.data['stats'].items() if isinstance(k, str) and k.endswith('_squad')
                }
            if not self.stats_lifetime:
                self.stats_lifetime = self.data['totals']

        return super().save(*args, **kwargs)


class Matches(models.Model):
    public_id = models.CharField(max_length=100, unique=True)
    player = models.ForeignKey(
        'players.Player', related_name='matches', on_delete=models.CASCADE,
    )
    data = JSONField(null=True)

    date_added = models.DateTimeField(auto_now_add=True)
    date_changed = models.DateTimeField(auto_now=True)


class Friend(models.Model):
    player = models.ForeignKey(
        'players.Player', related_name='friends', on_delete=models.CASCADE
    )

    date_added = models.DateTimeField(auto_now_add=True)
    date_changed = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.player.username
