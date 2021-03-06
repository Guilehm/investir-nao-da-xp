from itertools import islice

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from communications.utils import get_profile_data, get_stats_by_season
from core.forms import SearchForm
from core.models import Item, Platform, Season
from core.tasks import get_friends_status, get_items, get_upcoming_items_task
from players.models import Friend, Player


def index(request):
    friends = Friend.objects.all()
    platforms = Platform.objects.all()
    get_friends_status.delay()
    get_upcoming_items_task.delay()
    get_items.delay()
    return render(request, 'core/index.html', {
        'friends': friends,
        'platforms': platforms,
    })


def player_search(request):
    if not request.method == 'POST':
        return render(request, 'core/index.html')
    form = SearchForm(request.POST)
    if form.is_valid():
        username = form.cleaned_data['username']
        platform = form.cleaned_data['platforms']
        communication = get_profile_data(username, platform)
        if communication.error:
            messages.add_message(
                request,
                messages.ERROR,
                f'Usuário <strong>{username}</strong> não encontrado. '
                'Confira os dados ou selecione outra plataforma.'
            )
            return redirect(request.META.get('HTTP_REFERER'))
        return redirect('core:player-detail', username=communication.player_stats.player.username)


def player_detail(request, username):
    player = get_object_or_404(Player, username=username)
    platform = request.GET.get('platform')
    platforms = [platform.name for platform in player.platforms.all()]
    if platform not in platforms:
        platform = player.last_platform_name
    window_name = request.GET.get('window') or 'alltime'
    try:
        window = Season.objects.get(name=window_name)
    except Season.DoesNotExist:
        window, _ = Season.objects.get_or_create(name='alltime')
    status = player.statuses.filter(
        platform__name=platform, window=window, source='fortnite_tracker'
    ).last()
    seasons = Season.objects.only_available()
    # get_match_history(player.uid)  # TODO: Refactor
    return render(request, 'core/player_detail.html', {
        'player': player,
        'status': status,  # FIXME: Refactor
        'seasons': seasons,
        'season_name': window_name,
    })


def player_detail_by_season(request, username, season_number):
    player = get_object_or_404(Player, username=username)
    platform_name = player.last_platform_name
    try:
        if season_number == 0:
            raise ValueError
        season_name = 'season{number}'.format(number=int(season_number))
    except ValueError:
        return redirect('core:player-detail', username=username)
    window, _ = Season.objects.get_or_create(name=season_name)
    comm = get_stats_by_season(player.id, player.clean_uid, platform_name, window)
    stats = comm.player_stats if comm else None
    seasons = Season.objects.only_available()
    return render(request, 'core/player_detail_by_season.html', {
        'player': player,
        'stats': stats,  # FIXME: Refactor
        'seasons': seasons,
        'season_name': season_name,
    })


@cache_page(0.5 * 60)
def item_list(request):
    items = islice(Item.objects.order_by('?'), 4)
    items_upcoming = Item.objects.filter(is_upcoming=True)
    return render(request, 'core/items_all_list.html', {
        'items': items,
        'items_upcoming': items_upcoming,
    })


@cache_page(3 * 60)
def chart_list(request):
    season_name = request.GET.get('season', 'alltime')
    modes = ['solo', 'duo', 'squad']
    mode = request.GET.get('mode', 'squad').lower()
    if mode not in modes:
        mode = 'squad'
    try:
        season = Season.objects.get(name=season_name)
    except Season.DoesNotExist:
        season, _ = Season.objects.get_or_create(name='alltime')
    friends = Player.objects.filter(friends__isnull=False)
    all_stats = list()
    for friend in friends:
        comm = get_stats_by_season(
            friend.id, friend.clean_uid, friend.last_platform_name, season
        )
        all_stats.append(comm.player_stats if comm else None)
    seasons = Season.objects.only_available()
    return render(request, 'core/chart_list.html', {
        'season_name': season.name,
        'all_stats': all_stats,
        'mode': mode,
        'seasons': seasons,
    })
