import re

from django.conf import settings
from django.core import mail
from django.urls import reverse

from django.contrib.auth import get_user_model

users = (
    ('editor', 'editor'),
    ('reviewer', 'reviewer'),
    ('user', 'user'),
    ('api', 'api'),
    ('anonymous', None),
)


def test_get_profile_update(db, client):
    """
    An authorized GET request to the profile update form returns the form.
    """
    client.login(username='user', password='user')

    url = reverse('profile_update')
    response = client.get(url)
    assert response.status_code == 200


def test_get_profile_update_redirect(db, client):
    """
    An unauthorized GET request to the profile update form gets
    redirected to login.
    """
    url = reverse('profile_update')
    response = client.get(url)
    assert response.status_code == 302
    assert response.url == reverse('account_login') + '?next=' + url


def test_post_profile_update(db, client):
    """
    An authorized POST request to the profile update form updates the
    user and redirects to home.
    """
    client.login(username='user', password='user')

    url = reverse('profile_update')
    data = {
        'email': 'test@example.com',
        'first_name': 'Albert',
        'last_name': 'Admin',
        'text': 'text',
        'textarea': 'textarea'
    }
    response = client.post(url, data)

    if settings.PROFILE_UPDATE:
        assert response.status_code == 302
        assert response.url == reverse('home')
    else:
        assert response.status_code == 200


def test_post_profile_update_cancel(db, client):
    """
    An authorized POST request to the profile update form updates with
    cancel redirects to home.
    """
    client.login(username='user', password='user')

    url = reverse('profile_update')
    data = {
        'email': 'test@example.com',
        'first_name': 'Albert',
        'last_name': 'Admin',
        'cancel': 'cancel'
    }
    response = client.post(url, data)

    if settings.PROFILE_UPDATE:
        assert response.status_code == 302
        assert response.url == reverse('home')
    else:
        assert response.status_code == 200


def test_post_profile_update_cancel2(db, client):
    """
    An authorized POST request to the profile update form updates with
    cancel and the next field redirects to the given url.
    """
    client.login(username='user', password='user')

    url = reverse('profile_update')
    data = {
        'email': 'test@example.com',
        'first_name': 'Albert',
        'last_name': 'Admin',
        'cancel': 'cancel',
        'next': reverse('projects')
    }
    response = client.post(url, data)

    if settings.PROFILE_UPDATE:
        assert response.status_code == 302
        assert response.url == reverse('projects')
    else:
        assert response.status_code == 200


def test_post_profile_update_next(db, client):
    """
    An authorized POST request to the profile update form with next field
    updates the user and redirects to the given url.
    """
    client.login(username='user', password='user')

    url = reverse('profile_update')
    data = {
        'email': 'test@example.com',
        'first_name': 'Albert',
        'last_name': 'Admin',
        'text': 'text',
        'textarea': 'textarea',
        'next': reverse('projects')
    }
    response = client.post(url, data)

    if settings.PROFILE_UPDATE:
        assert response.status_code == 302
        assert response.url == reverse('projects')
    else:
        assert response.status_code == 200


def test_post_profile_update_next2(db, client):
    """
    An authorized POST request to the profile update form with next
    field set to profile_update updates the user and redirects to home.
    """
    client.login(username='user', password='user')

    url = reverse('profile_update')
    data = {
        'email': 'test@example.com',
        'first_name': 'Albert',
        'last_name': 'Admin',
        'text': 'text',
        'textarea': 'textarea',
        'next': reverse('profile_update')
    }
    response = client.post(url, data)

    if settings.PROFILE_UPDATE:
        assert response.status_code == 302
        assert response.url == reverse('home')
    else:
        assert response.status_code == 200


def test_password_change_get(db, client):
    """
    An authorized GET request to the password change form returns the form.
    """
    if settings.ACCOUNT:
        client.login(username='user', password='user')

        url = reverse('account_change_password')
        response = client.get(url)
        assert response.status_code == 200


def test_password_change_post(db, client):
    """
    An authorized POST request to the password change form updates the
    password and redirects to home.
    """
    if settings.ACCOUNT:
        client.login(username='user', password='user')

        url = reverse('account_change_password')
        data = {
            'old_password': 'user',
            'new_password1': 'resu',
            'new_password2': 'resu',
        }
        response = client.post(url, data)
        assert response.status_code == 200


def test_password_reset_get(db, client):
    """
    A GET request to the password reset form returns the form.
    """
    if settings.ACCOUNT:
        url = reverse('account_reset_password')
        response = client.get(url)
        assert response.status_code == 200


def test_password_reset_post_invalid(db, client):
    """
    A POST request to the password reset form with an invalid mail address
    sends no mail.
    """
    if settings.ACCOUNT:
        url = reverse('account_reset_password')
        data = {'email': 'wrong@example.com'}
        response = client.post(url, data)
        assert response.status_code == 200
        assert len(mail.outbox) == 0


def test_password_reset_post_valid(db, client):
    """
    A POST request to the password reset form with an invalid mail address
    sends a mail with a correct link.
    """
    if settings.ACCOUNT:
        url = reverse('account_reset_password')
        data = {'email': 'user@example.com'}
        response = client.post(url, data)
        assert response.status_code == 302
        assert response.url == reverse('account_reset_password_done')
        assert len(mail.outbox) == 1

        # get the link from the mail
        urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', mail.outbox[0].body)
        assert len(urls) == 1

        # get the password_reset page
        response = client.get(urls[0])
        assert response.status_code == 302
        assert response.url == reverse('account_reset_password_from_key', args=['4','set-password'])


def test_remove_user_get(db, client):
    if settings.PROFILE_DELETE:
        client.login(username='user', password='user')

        url = reverse('profile_remove')
        response = client.get(url)
        assert response.status_code == 200


def test_remove_user_post(db, client):
    if settings.PROFILE_DELETE:
        client.login(username='user', password='user')

        url = reverse('profile_remove')
        data = {
            'email': 'user@example.com',
            'password': 'user',
            'consent': True
        }
        response = client.post(url, data)
        assert response.status_code == 200
        assert not get_user_model().objects.filter(username='user').exists()


def test_remove_user_post_invalid_email(db, client):
    if settings.PROFILE_DELETE:
        client.login(username='user', password='user')

        url = reverse('profile_remove')
        data = {
            'email': 'invalid',
            'password': 'user',
            'consent': True
        }
        response = client.post(url, data)
        assert response.status_code == 200
        assert get_user_model().objects.filter(username='user').exists()


def test_remove_user_post_invalid_password(db, client):
    if settings.PROFILE_DELETE:
        client.login(username='user', password='user')

        url = reverse('profile_remove')
        data = {
            'email': 'user@example.com',
            'password': 'invalid',
            'consent': True
        }
        response = client.post(url, data)
        assert response.status_code == 200
        assert get_user_model().objects.filter(username='user').exists()


def test_remove_user_post_invalid_consent(db, client):
    if settings.PROFILE_DELETE:
        client.login(username='user', password='user')

        url = reverse('profile_remove')
        data = {
            'email': 'user@example.com',
            'password': 'user',
            'consent': False
        }

        response = client.post(url, data)
        assert response.status_code == 200
        assert get_user_model().objects.filter(username='user').exists()


def test_signup(db, client):
    url = reverse('account_signup')
    response = client.post(url, {
        'email': 'test@example.com',
        'username': 'test',
        'first_name': 'test',
        'last_name': 'test',
        'password1': 'test',
        'password2': 'test',
    })

    assert response.status_code == 302
    assert response.url == '/'


def test_signup_next(db, client):
    url = reverse('account_signup') + '?next=/about/'
    response = client.post(url, {
        'email': 'test@example.com',
        'username': 'test',
        'first_name': 'test',
        'last_name': 'test',
        'password1': 'test',
        'password2': 'test',
    })

    assert response.status_code == 302
    assert response.url == '/about/'
