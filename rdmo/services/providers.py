import hmac
import json
import logging
from urllib.parse import quote, urlencode

import requests
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.utils.crypto import get_random_string
from django.utils.translation import gettext_lazy as _
from rdmo.core.plugins import Plugin

logger = logging.getLogger(__name__)


class Provider(Plugin):

    def send_issue(self, request, issue, integration, subject, message, attachments):
        raise NotImplementedError

    def webhook(self, request, options, payload):
        raise NotImplementedError


class OauthProvider(Provider):

    def send_issue(self, request, issue, integration, subject, message, attachments):
        url = self.get_post_url(request, issue, integration, subject, message, attachments)
        data = self.get_post_data(request, issue, integration, subject, message, attachments)

        if url is None or data is None:
            return render(request, 'core/error.html', {
                'title': _('Integration error'),
                'errors': [_('The Integration is not configured correctly.') % message]
            }, status=200)

        return self.post(request, url, data, issue.id, integration.id)

    def post(self, request, url, data, issue_id, integration_id):
        # get access token from the session
        access_token = self.get_from_session(request, 'access_token')
        if access_token:
            logger.debug('post: %s %s', url, data)

            response = requests.post(url, json=data, headers=self.get_authorization_headers(access_token))

            if response.status_code == 401:
                logger.warn('post forbidden: %s (%s)', response.content, response.status_code)
            else:
                try:
                    response.raise_for_status()
                    remote_url = self.get_issue_url(response)
                    self.update_issue(issue_id, integration_id, remote_url)
                    return HttpResponseRedirect(remote_url)
                except requests.HTTPError:
                    logger.warn('post error: %s (%s)', response.content, response.status_code)

                    message = response.json().get('error')
                    return render(request, 'core/error.html', {
                        'title': _('Send error'),
                        'errors': [_('Something went wrong: %s.') % message]
                    }, status=200)

        # if the above did not work authorize first
        self.store_in_session(request, 'post', (url, data, issue_id, integration_id))
        return self.authorize(request)

    def authorize(self, request):
        # get random state and store in session
        state = get_random_string(length=32)
        self.store_in_session(request, 'state', state)

        url = self.authorize_url + '?' + urlencode(self.get_authorize_params(request, state))
        return HttpResponseRedirect(url)

    def callback(self, request):
        assert request.GET.get('state') == self.pop_from_session(request, 'state')

        url = self.token_url + '?' + urlencode(self.get_callback_params(request))

        response = requests.post(url, headers={
            'Accept': 'application/json'
        })

        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            logger.error('callback error: %s (%s)', response.content, response.status_code)
            raise e

        response_data = response.json()

        # store access token in session
        self.store_in_session(request, 'access_token', response_data.get('access_token'))

        # get post data from session
        try:
            url, data, issue_id, integration_id = self.pop_from_session(request, 'post')
            return self.post(request, url, data, issue_id, integration_id)
        except ValueError:
            return render(request, 'core/error.html', {
                'title': _('Authorization successful'),
                'errors': [_('But no redirect could be found.')]
            }, status=200)

    def update_issue(self, issue_id, integration_id, remote_url):
        from rdmo.projects.models import Issue, Integration, IssueResource
        try:
            issue = Issue.objects.get(pk=issue_id)
            issue.status = Issue.ISSUE_STATUS_IN_PROGRESS
            issue.save()

            integration = Integration.objects.get(pk=integration_id)

            issue_resource = IssueResource(issue=issue, integration=integration, url=remote_url)
            issue_resource.save()
        except ObjectDoesNotExist:
            pass

    def get_session_key(self, key):
        class_name = self.__class__.__name__.lower()
        return '{}_{}'.format(class_name, key)

    def store_in_session(self, request, key, data):
        session_key = self.get_session_key(key)
        request.session[session_key] = data

    def get_from_session(self, request, key):
        session_key = self.get_session_key(key)
        return request.session.get(session_key, None)

    def pop_from_session(self, request, key):
        session_key = self.get_session_key(key)
        return request.session.pop(session_key, None)

    def get_post_url(self, request, issue, integration, subject, message, attachments):
        raise NotImplementedError

    def get_post_data(self, request, issue, integration, subject, message, attachments):
        raise NotImplementedError

    def get_authorization_headers(self, access_token):
        raise NotImplementedError

    def get_authorize_params(self, request, state):
        raise NotImplementedError

    def get_callback_params(self, request):
        raise NotImplementedError

    def get_issue_url(self, response):
        raise NotImplementedError


class GitHubProvider(OauthProvider):
    add_label = _('Add GitHub integration')
    send_label = _('Send to GitHub')
    description = _('This integration allow the creation of issues in arbitrary GitHub repositories. '
                    'The upload of attachments is not supported by GitHub.')

    authorize_url = 'https://github.com/login/oauth/authorize'
    token_url = 'https://github.com/login/oauth/access_token'

    @property
    def client_id(self):
        return settings.GITHUB_PROVIDER['client_id']

    @property
    def client_secret(self):
        return settings.GITHUB_PROVIDER['client_secret']

    @property
    def redirect_path(self):
        return reverse('oauth_callback', args=['github'])

    def get_repo(self, integration):
        try:
            return integration.options.get(key='repo').value
        except ObjectDoesNotExist:
            return None

    def get_secret(self, integration):
        try:
            return integration.options.get(key='secret').value
        except ObjectDoesNotExist:
            return None

    def get_post_url(self, request, issue, integration, subject, message, attachments):
        repo = self.get_repo(integration)
        if repo:
            return 'https://api.github.com/repos/{}/issues'.format(repo)

    def get_post_data(self, request, issue, integration, subject, message, attachments):
        return {
            'title': subject,
            'body': message
        }

    def get_authorization_headers(self, access_token):
        return {
            'Authorization': 'token {}'.format(access_token),
            'Accept': 'application/vnd.github.v3+json'
        }

    def get_authorize_params(self, request, state):
        return {
            'authorize_url': self.authorize_url,
            'client_id': self.client_id,
            'redirect_uri': request.build_absolute_uri(self.redirect_path),
            'scope': 'repo',
            'state': state,
        }

    def get_callback_params(self, request):
        return {
            'token_url': self.token_url,
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': request.GET.get('code')
        }

    def get_issue_url(self, response):
        return response.json().get('html_url')

    def webhook(self, request, integration):
        secret = self.get_secret(integration)
        header_signature = request.headers.get('X-Hub-Signature')

        if (secret is not None) and (header_signature is not None):
            body_signature = 'sha1=' + hmac.new(secret.encode(), request.body, 'sha1').hexdigest()

            if hmac.compare_digest(header_signature, body_signature):
                try:
                    payload = json.loads(request.body.decode())
                    action = payload.get('action')
                    issue_url = payload.get('issue', {}).get('html_url')

                    if action and issue_url:
                        try:
                            issue_resource = integration.resources.get(url=issue_url)
                            if action == 'closed':
                                issue_resource.issue.status = issue_resource.issue.ISSUE_STATUS_CLOSED
                            else:
                                issue_resource.issue.status = issue_resource.issue.ISSUE_STATUS_IN_PROGRESS

                            issue_resource.issue.save()
                        except ObjectDoesNotExist:
                            pass

                    return HttpResponse(status=200)

                except json.decoder.JSONDecodeError as e:
                    return HttpResponse(e, status=400)

        raise Http404

    @property
    def fields(self):
        return [
            {
                'key': 'repo',
                'placeholder': 'user_name/repo_name',
                'help': _('The GitHub repository to send issues to.')
            },
            {
                'key': 'secret',
                'placeholder': 'Secret (random) string',
                'help': _('The secret for a GitHub webhook to close a task.'),
                'required': False,
                'secret': True
            }
        ]


class GitLabProvider(OauthProvider):
    add_label = _('Add GitLab integration')
    send_label = _('Send to GitLab')

    @property
    def gitlab_url(self):
        return settings.GITLAB_PROVIDER['gitlab_url'].strip('/')

    @property
    def description(self):
        return _('This integration allow the creation of issues in arbitrary repositories on {}. '
                 'The upload of attachments is not supported by GitLab.'.format(self.gitlab_url))

    @property
    def authorize_url(self):
        return '{}/oauth/authorize'.format(self.gitlab_url)

    @property
    def token_url(self):
        return '{}/oauth/token'.format(self.gitlab_url)

    @property
    def client_id(self):
        return settings.GITLAB_PROVIDER['client_id']

    @property
    def client_secret(self):
        return settings.GITLAB_PROVIDER['client_secret']

    @property
    def redirect_path(self):
        return reverse('oauth_callback', args=['gitlab'])

    def get_repo(self, integration):
        try:
            return integration.options.get(key='repo').value
        except ObjectDoesNotExist:
            return None

    def get_secret(self, integration):
        try:
            return integration.options.get(key='secret').value
        except ObjectDoesNotExist:
            return None

    def get_post_url(self, request, issue, integration, subject, message, attachments):
        repo = self.get_repo(integration)
        if repo:
            return '{}/api/v4/projects/{}/issues'.format(self.gitlab_url, quote(repo, safe=''))

    def get_post_data(self, request, issue, integration, subject, message, attachments):
        return {
            'title': subject,
            'description': message
        }

    def get_authorization_headers(self, access_token):
        return {
            'Authorization': 'Bearer {}'.format(access_token)
        }

    def get_authorize_params(self, request, state):
        return {
            'authorize_url': self.authorize_url,
            'client_id': self.client_id,
            'redirect_uri': request.build_absolute_uri(self.redirect_path),
            'response_type': 'code',
            'scope': 'api',
            'state': state,
        }

    def get_callback_params(self, request):
        return {
            'token_url': self.token_url,
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': request.GET.get('code'),
            'grant_type': 'authorization_code',
            'redirect_uri': request.build_absolute_uri(self.redirect_path)
        }

    def get_issue_url(self, response):
        return response.json().get('web_url')

    def webhook(self, request, integration):
        secret = self.get_secret(integration)
        header_token = request.headers.get('X-Gitlab-Token')

        if (secret is not None) and (header_token is not None) and (header_token == secret):
            try:
                payload = json.loads(request.body.decode())
                state = payload.get('object_attributes', {}).get('state')
                issue_url = payload.get('object_attributes', {}).get('url')

                if state and issue_url:
                    try:
                        issue_resource = integration.resources.get(url=issue_url)
                        if state == 'closed':
                            issue_resource.issue.status = issue_resource.issue.ISSUE_STATUS_CLOSED
                        else:
                            issue_resource.issue.status = issue_resource.issue.ISSUE_STATUS_IN_PROGRESS

                        issue_resource.issue.save()
                    except ObjectDoesNotExist:
                        pass

                return HttpResponse(status=200)

            except json.decoder.JSONDecodeError as e:
                return HttpResponse(e, status=400)

        raise Http404

    @property
    def fields(self):
        return [
            {
                'key': 'repo',
                'placeholder': 'user_name/repo_name',
                'help': _('The GitLab repository to send issues to.')
            },
            {
                'key': 'secret',
                'placeholder': 'Secret (random) string',
                'help': _('The secret for a GitLab webhook to close a task.'),
                'required': False,
                'secret': True
            }
        ]
