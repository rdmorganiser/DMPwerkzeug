import pytest
from django.urls import reverse

from ..models import Issue

users = (
    ('owner', 'owner'),
    ('manager', 'manager'),
    ('author', 'author'),
    ('guest', 'guest'),
    ('api', 'api'),
    ('user', 'user'),
    ('site', 'site'),
    ('anonymous', None),
)

view_issue_permission_map = {
    'owner': [1, 2, 3, 4, 5],
    'manager': [1, 3, 5],
    'author': [1, 3, 5],
    'guest': [1, 3, 5],
    'api': [1, 2, 3, 4, 5],
    'site': [1, 2, 3, 4, 5]
}

urlnames = {
    'list': 'v1-projects:issue-list',
    'detail': 'v1-projects:issue-detail'
}

projects = [1, 2, 3, 4, 5]
issues = [1, 2, 3, 4]

site_id = 1
project_id = 1
project_count = 4

issue_status = ('open', 'in_progress', 'closed')


@pytest.mark.parametrize('username,password', users)
def test_list(db, client, username, password):
    client.login(username=username, password=password)

    url = reverse(urlnames['list'])
    response = client.get(url)

    if password:
        assert response.status_code == 200
        assert isinstance(response.json(), list)

        if username == 'user':
            assert sorted([item['id'] for item in response.json()]) == []
        else:
            values_list = Issue.objects.filter(project__in=view_issue_permission_map.get(username, [])) \
                                       .order_by('id').values_list('id', flat=True)
            assert sorted([item['id'] for item in response.json()]) == list(values_list)
    else:
        assert response.status_code == 401


@pytest.mark.parametrize('username,password', users)
@pytest.mark.parametrize('issue_id', issues)
def test_detail(db, client, username, password, issue_id):
    client.login(username=username, password=password)
    issue = Issue.objects.get(id=issue_id)

    url = reverse(urlnames['detail'], args=[issue_id])
    response = client.get(url)

    if issue.project.id in view_issue_permission_map.get(username, []):
        assert response.status_code == 200
        assert isinstance(response.json(), dict)
        assert response.json().get('id') == issue_id
    elif password:
        assert response.status_code == 404
    else:
        assert response.status_code == 401


@pytest.mark.parametrize('username,password', users)
def test_create(db, client, username, password):
    client.login(username=username, password=password)

    url = reverse(urlnames['list'])
    response = client.post(url)

    if password:
        assert response.status_code == 405
    else:
        assert response.status_code == 401


@pytest.mark.parametrize('username,password', users)
@pytest.mark.parametrize('issue_id', issues)
def test_update(db, client, username, password, issue_id):
    client.login(username=username, password=password)

    url = reverse(urlnames['detail'], args=[issue_id])
    data = {}
    response = client.put(url, data, content_type='application/json')

    if password:
        assert response.status_code == 405
    else:
        assert response.status_code == 401


@pytest.mark.parametrize('username,password', users)
@pytest.mark.parametrize('issue_id', issues)
def test_delete(db, client, username, password, issue_id):
    client.login(username=username, password=password)

    url = reverse(urlnames['detail'], args=[issue_id])
    response = client.delete(url)

    if password:
        assert response.status_code == 405
    else:
        assert response.status_code == 401
