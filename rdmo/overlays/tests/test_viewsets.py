import pytest
from django.urls import reverse

from ..models import Overlay

users = (
    ('user', 'user'),
    ('anonymous', None)
)

urlnames = {
    'current': 'v1-overlays:overlay-current',
    'next': 'v1-overlays:overlay-next',
    'dismiss': 'v1-overlays:overlay-dismiss'
}

url_names = [
    'projects'
]


@pytest.mark.parametrize('username,password', users)
@pytest.mark.parametrize('url_name', url_names)
def test_current(db, client, username, password, url_name):
    client.login(username=username, password=password)

    url = reverse(urlnames['current'], args=[url_name])
    response = client.post(url)

    if password:
        assert response.status_code == 200
        assert Overlay.objects.get(user__username=username, url_name=url_name).current == response.json().get('overlay')
    else:
        assert response.status_code == 401


@pytest.mark.parametrize('username,password', users)
@pytest.mark.parametrize('url_name', url_names)
def test_next(db, client, username, password, url_name):
    client.login(username=username, password=password)

    url = reverse(urlnames['next'], args=[url_name])
    response = client.post(url)

    if password:
        assert response.status_code == 200
        assert response.json().get('overlay') == Overlay.objects.get(
            user__username=username, url_name=url_name
        ).current
    else:
        assert response.status_code == 401


@pytest.mark.parametrize('username,password', users)
@pytest.mark.parametrize('url_name', url_names)
def test_dismiss(db, client, username, password, url_name):
    client.login(username=username, password=password)

    url = reverse(urlnames['dismiss'], args=[url_name])
    response = client.post(url)

    if password:
        assert response.status_code == 200
        assert response.json().get('overlay') == ''
        assert response.json().get('overlay') == Overlay.objects.get(
            user__username=username, url_name=url_name
        ).current
    else:
        assert response.status_code == 401
