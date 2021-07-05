import pytest
from django.urls import reverse

from ..models import Project

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

view_project_permission_map = {
    'owner': [1, 2, 3, 4, 5],
    'manager': [1, 3, 5],
    'author': [1, 3, 5],
    'guest': [1, 3, 5],
    'api': [1, 2, 3, 4, 5],
    'site': [1, 2, 3, 4, 5]
}

change_project_permission_map = {
    'owner': [1, 2, 3, 4, 5],
    'manager': [1, 3, 5],
    'api': [1, 2, 3, 4, 5],
    'site': [1, 2, 3, 4, 5]
}

delete_project_permission_map = {
    'owner': [1, 2, 3, 4, 5],
    'api': [1, 2, 3, 4, 5],
    'site': [1, 2, 3, 4, 5]
}

urlnames = {
    'list': 'v1-projects:project-list',
    'detail': 'v1-projects:project-detail',
    'overview': 'v1-projects:project-overview',
    'resolve': 'v1-projects:project-resolve',
    'progress': 'v1-projects:project-progress'
}

projects = [1, 2, 3, 4, 5]
conditions = [1]

project_values = 37
project_total = 54
catalog_id = 1


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
            values_list = Project.objects.filter(id__in=view_project_permission_map.get(username, [])) \
                                         .order_by('id').values_list('id', flat=True)
            assert sorted([item['id'] for item in response.json()]) == list(values_list)
    else:
        assert response.status_code == 401


@pytest.mark.parametrize('username,password', users)
@pytest.mark.parametrize('project_id', projects)
def test_detail(db, client, username, password, project_id):
    client.login(username=username, password=password)

    url = reverse(urlnames['detail'], args=[project_id])
    response = client.get(url)

    if project_id in view_project_permission_map.get(username, []):
        assert response.status_code == 200
        assert isinstance(response.json(), dict)
        assert response.json().get('id') == project_id
    else:
        if password:
            assert response.status_code == 404
        else:
            assert response.status_code == 401


@pytest.mark.parametrize('username,password', users)
def test_create(db, client, username, password):
    client.login(username=username, password=password)

    url = reverse(urlnames['list'])
    data = {
        'title': 'Lorem ipsum dolor sit amet',
        'description': 'At vero eos et accusam et justo duo dolores et ea rebum.',
        'catalog': catalog_id
    }
    response = client.post(url, data)

    if password:
        assert response.status_code == 201
        assert isinstance(response.json(), dict)
        assert Project.objects.get(id=response.json().get('id'))
    else:
        assert response.status_code == 401


@pytest.mark.parametrize('username,password', users)
@pytest.mark.parametrize('project_id', projects)
def test_create_parent(db, client, username, password, project_id):
    client.login(username=username, password=password)

    url = reverse(urlnames['list'])
    data = {
        'title': 'Lorem ipsum dolor sit amet',
        'description': 'At vero eos et accusam et justo duo dolores et ea rebum.',
        'catalog': catalog_id,
        'parent': project_id
    }
    response = client.post(url, data)

    if project_id in view_project_permission_map.get(username, []):
        assert response.status_code == 201
        assert isinstance(response.json(), dict)
        assert Project.objects.get(id=response.json().get('id'))
    else:
        if password:
            assert response.status_code == 400
        else:
            assert response.status_code == 401


@pytest.mark.parametrize('username,password', users)
@pytest.mark.parametrize('project_id', projects)
def test_update(db, client, username, password, project_id):
    client.login(username=username, password=password)
    project = Project.objects.get(pk=project_id)

    url = reverse(urlnames['detail'], args=[project_id])
    data = {
        'title': 'New title',
        'description': project.description,
        'catalog': project.catalog.id
    }
    response = client.put(url, data, content_type='application/json')

    if project_id in change_project_permission_map.get(username, []):
        assert response.status_code == 200
        assert Project.objects.get(id=project_id).title == 'New title'
        assert Project.objects.get(id=project_id).description == project.description
    else:
        if project_id in view_project_permission_map.get(username, []):
            assert response.status_code == 403
        elif password:
            assert response.status_code == 404
        else:
            assert response.status_code == 401

        assert Project.objects.get(id=project_id).title == project.title
        assert Project.objects.get(id=project_id).description == project.description


@pytest.mark.parametrize('username,password', users)
@pytest.mark.parametrize('project_id', projects)
def test_delete(db, client, username, password, project_id):
    client.login(username=username, password=password)

    url = reverse(urlnames['detail'], args=[project_id])
    response = client.delete(url)

    if project_id in delete_project_permission_map.get(username, []):
        assert response.status_code == 204
        assert Project.objects.filter(id=project_id).first() is None
    else:
        if project_id in view_project_permission_map.get(username, []):
            assert response.status_code == 403
        elif password:
            assert response.status_code == 404
        else:
            assert response.status_code == 401

        assert Project.objects.filter(id=project_id).first()


@pytest.mark.parametrize('username,password', users)
@pytest.mark.parametrize('project_id', projects)
@pytest.mark.parametrize('condition_id', conditions)
def test_overview(db, client, username, password, project_id, condition_id):
    client.login(username=username, password=password)

    url = reverse(urlnames['overview'], args=[project_id])
    response = client.get(url)

    if project_id in view_project_permission_map.get(username, []):
        assert response.status_code == 200
        assert isinstance(response.json(), dict)
        assert response.json().get('id') == project_id
    else:
        if password:
            assert response.status_code == 404
        else:
            assert response.status_code == 401


@pytest.mark.parametrize('username,password', users)
@pytest.mark.parametrize('project_id', projects)
@pytest.mark.parametrize('condition_id', conditions)
def test_resolve(db, client, username, password, project_id, condition_id):
    client.login(username=username, password=password)

    url = reverse(urlnames['resolve'], args=[project_id]) + '?condition={}'.format(condition_id)
    response = client.get(url)

    if project_id in view_project_permission_map.get(username, []):
        assert response.status_code == 200
        assert isinstance(response.json(), dict)
    else:
        if password:
            assert response.status_code == 404
        else:
            assert response.status_code == 401


@pytest.mark.parametrize('username,password', users)
@pytest.mark.parametrize('project_id', projects)
def test_progress(db, client, username, password, project_id):
    client.login(username=username, password=password)

    url = reverse(urlnames['progress'], args=[project_id])
    response = client.get(url)

    if project_id in view_project_permission_map.get(username, []):
        assert response.status_code == 200
        assert isinstance(response.json(), dict)

        if project_id == 1:
            assert response.json().get('values') == project_values
        else:
            assert response.json().get('values') == 1

        assert response.json().get('total') == project_total
    else:
        if password:
            assert response.status_code == 404
        else:
            assert response.status_code == 401
