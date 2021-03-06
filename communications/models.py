import uuid

import requests
from django.contrib.postgres.fields import JSONField
from django.db import models

from core.models import Platform, Season
from players.models import Matches, Player, PlayerStats
from xp.settings import TRN_API_KEY

HEADERS = {'TRN-Api-Key': TRN_API_KEY}
URLS = {
    'profile_data': 'https://api.fortnitetracker.com/v1/profile/{platform}/{username}',
    'match_history': 'https://api.fortnitetracker.com/v1/profile/account/{account_id}/matches',
    'stats_by_season': 'https://fortnite-public-api.theapinetwork.com/prod09/users/public/br_stats?'
                       'user_id={user_uid}&platform={platform}&window={window}',
    'all_items': 'https://fortnite-public-api.theapinetwork.com/prod09/items/list',
    'upcoming_items': 'https://fortnite-public-api.theapinetwork.com/prod09/upcoming/get',
    'daily_store': 'https://fortnite-public-api.theapinetwork.com/prod09/store/get',
}


class Communication(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    method = models.CharField(max_length=100)
    url = models.URLField(max_length=200, null=True)
    data = JSONField(null=True, blank=True)
    player_stats = models.OneToOneField(
        'players.PlayerStats',
        related_name='communication',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    error = models.BooleanField(default=True)

    date_added = models.DateTimeField(auto_now_add=True)
    date_changed = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-date_added',)

    def __str__(self):
        return f'Communication #{self.id}'

    def communicate_get_items(self):
        url = URLS.get(self.method)
        response = requests.get(url)
        self.data = response.json()
        self.url = url
        if response.ok:
            self.error = False
        self.save()
        return self

    def communicate_gaming_sdk(self, user_uid, platform, window):
        platforms = {
            'pc': 'pc',
            'psn': 'ps4',
            'xbox': 'xb1',
        }
        url = URLS.get(self.method).format(
            user_uid=user_uid, platform=platforms.get(platform), window=window
        )
        response = requests.get(url)
        self.data = response.json()
        self.url = url
        if response.ok:
            if self.data.get('response') == 200:
                self.error = False
        self.save()
        return self

    def communicate(self, **data):
        url = URLS.get(self.method).format(**data)
        response = requests.get(
            url=url,
            headers=HEADERS,
            data=dict(data),
        )
        self.data = response.json()
        self.url = url
        if response.ok:  # TODO: Improve validation
            try:
                error = self.data.get('error')
            except AttributeError:
                self.error = False
            else:
                if not error:
                    self.error = False
        self.save()
        return self

    def _get_platform(self):
        if not self.error:
            platform, created = Platform.objects.get_or_create(
                name=self.data.get('platformName')
            )
            save = False
            if not platform.epic_id:
                platform.epic_id = self.data.get('platformId')
                save = True
            if not platform.name_long:
                platform.name_long = self.data.get('platformNameLong')
                save = True
            if save:
                platform.save()
            return platform

    def _get_player(self):
        if not self.data.get('error'):
            player, _ = Player.objects.get_or_create(
                uid=self.data.get('accountId'),
                username=self.data.get('epicUserHandle'),
            )
            return player

    def create_player_stats(self):
        if not self.error:
            player = self._get_player()
            platform = self._get_platform()
            player.platforms.add(platform)
            season, _ = Season.objects.get_or_create(name='alltime')
            player_stats = PlayerStats.objects.create(
                player=player,
                platform=platform,
                data=self.data,
                window=season,
                source=PlayerStats.SOURCE_FORTNITE_TRACKER,
            )
            self.player_stats = player_stats
            player_stats.save()
            self.save()

    def create_player_stats_by_season(self, player, platform):
        if not self.error:
            season_name = self.data.get('window')
            season, _ = Season.objects.get_or_create(name=season_name)
            player_stats = PlayerStats.objects.create(
                player=player,
                platform=platform,
                data=self.data,
                source=PlayerStats.SOURCE_PUBLIC_API,
            )
            self.player_stats = player_stats
            self.save()

    def create_matches(self, account_id):
        if not self.error:
            player = Player.objects.get(uid=account_id)
            for m in self.data:
                match, _ = Matches.objects.get_or_create(
                    public_id=m['id'],
                    player=player,
                )
                match.data = m
                match.save()
