from django import forms
from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator
from django.db.models import Q
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from markdown import markdown

from rdmo.core.constants import VALUE_TYPE_FILE
from rdmo.core.plugins import get_plugin

from .constants import ROLE_CHOICES
from .models import (Integration, IntegrationOption, Invite, Membership,
                     Project, Snapshot)


class CatalogChoiceField(forms.ModelChoiceField):

    def label_from_instance(self, obj):
        return mark_safe('<b>%s</b></br>%s' % (obj.title, markdown(obj.help)))


class TasksMultipleChoiceField(forms.ModelMultipleChoiceField):

    def label_from_instance(self, obj):
        return mark_safe('<b>%s</b></br>%s' % (obj.title, markdown(obj.text)))


class ViewsMultipleChoiceField(forms.ModelMultipleChoiceField):

    def label_from_instance(self, obj):
        return mark_safe('<b>%s</b></br>%s' % (obj.title, markdown(obj.help)))


class ProjectForm(forms.ModelForm):

    use_required_attribute = False

    def __init__(self, *args, **kwargs):
        catalogs = kwargs.pop('catalogs')
        projects = kwargs.pop('projects')
        super().__init__(*args, **kwargs)
        self.fields['title'].widget.attrs.update({
            'autofocus': True
        })
        self.fields['catalog'].queryset = catalogs
        self.fields['catalog'].empty_label = None
        self.fields['catalog'].initial = catalogs.first()

        if settings.NESTED_PROJECTS:
            self.fields['parent'].queryset = projects

    class Meta:
        model = Project

        fields = ['title', 'description', 'catalog']
        if settings.NESTED_PROJECTS:
            fields += ['parent']

        field_classes = {
            'catalog': CatalogChoiceField
        }
        widgets = {
            'catalog': forms.RadioSelect()
        }


class ProjectUpdateInformationForm(forms.ModelForm):

    use_required_attribute = False

    class Meta:
        model = Project
        fields = ('title', 'description')


class ProjectUpdateCatalogForm(forms.ModelForm):

    use_required_attribute = False

    def __init__(self, *args, **kwargs):
        catalogs = kwargs.pop('catalogs')
        super().__init__(*args, **kwargs)
        self.fields['catalog'].queryset = catalogs
        self.fields['catalog'].empty_label = None

    class Meta:
        model = Project
        fields = ('catalog', )
        field_classes = {
            'catalog': CatalogChoiceField
        }
        widgets = {
            'catalog': forms.RadioSelect()
        }


class ProjectUpdateTasksForm(forms.ModelForm):

    use_required_attribute = False

    def __init__(self, *args, **kwargs):
        tasks = kwargs.pop('tasks')
        super().__init__(*args, **kwargs)
        self.fields['tasks'].queryset = tasks

    class Meta:
        model = Project
        fields = ('tasks', )
        field_classes = {
            'tasks': TasksMultipleChoiceField
        }
        widgets = {
            'tasks': forms.CheckboxSelectMultiple()
        }


class ProjectUpdateViewsForm(forms.ModelForm):

    use_required_attribute = False

    def __init__(self, *args, **kwargs):
        views = kwargs.pop('views')
        super().__init__(*args, **kwargs)
        self.fields['views'].queryset = views

    class Meta:
        model = Project
        fields = ('views', )
        field_classes = {
            'views': ViewsMultipleChoiceField
        }
        widgets = {
            'views': forms.CheckboxSelectMultiple()
        }


class ProjectUpdateParentForm(forms.ModelForm):

    use_required_attribute = False

    def __init__(self, *args, **kwargs):
        projects = kwargs.pop('projects')
        super().__init__(*args, **kwargs)
        self.fields['parent'].queryset = projects

    class Meta:
        model = Project
        fields = ('parent', )


class SnapshotCreateForm(forms.ModelForm):

    use_required_attribute = False

    class Meta:
        model = Snapshot
        fields = ('title', 'description')

    def __init__(self, *args, **kwargs):
        self.project = kwargs.pop('project')
        super(SnapshotCreateForm, self).__init__(*args, **kwargs)

    def save(self, *args, **kwargs):
        self.instance.project = self.project
        return super(SnapshotCreateForm, self).save(*args, **kwargs)


class MembershipCreateForm(forms.Form):

    use_required_attribute = False

    username_or_email = forms.CharField(widget=forms.TextInput(attrs={'placeholder': _('Username or email')}),
                                        label=_('User'),
                                        help_text=_('The username or email of the new user.'))
    role = forms.CharField(widget=forms.RadioSelect(choices=ROLE_CHOICES),
                           initial='author')

    def __init__(self, *args, **kwargs):
        self.project = kwargs.pop('project')
        self.is_site_manager = kwargs.pop('is_site_manager')
        super().__init__(*args, **kwargs)

        if self.is_site_manager:
            self.fields['silent'] = forms.BooleanField(
                required=False,
                label=_('Add member silently'),
                help_text=_('As site manager or admin, you can directly add users without notifying them via email, when you check the following checkbox.')
            )

    def clean_username_or_email(self):
        username_or_email = self.cleaned_data['username_or_email']

        # check if it is a registered
        try:
            self.cleaned_data['user'] = User.objects.get(Q(username=username_or_email) | Q(email=username_or_email))
            self.cleaned_data['email'] = self.cleaned_data['user'].email

            if self.cleaned_data['user'] in self.project.user.all():
                raise ValidationError(_('The user is already a member of the project.'))

        except User.DoesNotExist:
            if settings.PROJECT_SEND_INVITE:
                # check if it is a valid email address, this will raise the correct ValidationError
                EmailValidator()(username_or_email)

                self.cleaned_data['user'] = None
                self.cleaned_data['email'] = username_or_email
            else:
                self.cleaned_data['user'] = None
                self.cleaned_data['email'] = None
                raise ValidationError(_('A user with this username or email was not found. Only registered users can be invited.'))

    def clean(self):
        if self.cleaned_data.get('silent') is True and self.cleaned_data['user'] is None:
            raise ValidationError(_('Only existing users can be added silently.'))

    def save(self):
        if self.is_site_manager and self.cleaned_data.get('silent') is True:
            Membership.objects.create(
                project=self.project,
                user=self.cleaned_data.get('user'),
                role=self.cleaned_data.get('role')
            )
        else:
            invite, created = Invite.objects.get_or_create(
                project=self.project,
                user=self.cleaned_data.get('user'),
                email=self.cleaned_data.get('email')
            )
            invite.role = self.cleaned_data.get('role')
            invite.make_token()
            invite.save()

            return invite


class IntegrationForm(forms.ModelForm):

    class Meta:
        model = Integration
        fields = ()

    def __init__(self, *args, **kwargs):
        self.project = kwargs.pop('project')
        self.provider_key = kwargs.pop('provider_key', None)
        super().__init__(*args, **kwargs)

        # get the provider
        if self.provider_key:
            self.provider = get_plugin('SERVICE_PROVIDERS', self.provider_key)
        else:
            self.provider = self.instance.provider

        # add fields for the integration options
        for field in self.provider.fields:
            try:
                initial = IntegrationOption.objects.get(integration=self.instance, key=field.get('key')).value
            except IntegrationOption.DoesNotExist:
                initial = None

            if field.get('placeholder'):
                attrs = {'placeholder': field.get('placeholder')}
            self.fields[field.get('key')] = forms.CharField(widget=forms.TextInput(attrs=attrs),
                                                            initial=initial, required=field.get('required', True))

    def save(self):
        # the the project and the provider_key
        self.instance.project = self.project
        if self.provider_key:
            self.instance.provider_key = self.provider_key

        # call the form's save method
        super().save()

        # save the integration options
        self.instance.save_options(self.cleaned_data)


class IssueSendForm(forms.Form):

    class AttachmentViewsField(forms.ModelMultipleChoiceField):
        def label_from_instance(self, obj):
            return _('Attach %s') % obj.title

    class AttachmentFilesField(forms.ModelMultipleChoiceField):
        def label_from_instance(self, obj):
            return _('Attach %s') % obj.file_name

    class AttachmentSnapshotField(forms.ModelChoiceField):
        def label_from_instance(self, obj):
            return obj.title

    subject = forms.CharField(label=_('Subject'), max_length=128)
    message = forms.CharField(label=_('Message'), widget=forms.Textarea)

    def __init__(self, *args, **kwargs):
        self.project = kwargs.pop('project')
        super().__init__(*args, **kwargs)

        self.fields['attachments_answers'] = forms.MultipleChoiceField(
            label=_('Answers'), widget=forms.CheckboxSelectMultiple, required=False,
            choices=[('project_answers', _('Attach the output of "View answers".'))]
        )
        self.fields['attachments_views'] = self.AttachmentViewsField(
            label=_('Views'), widget=forms.CheckboxSelectMultiple, required=False,
            queryset=self.project.views.all(), to_field_name='id'
        )
        self.fields['attachments_files'] = self.AttachmentFilesField(
            label=_('Files'), widget=forms.CheckboxSelectMultiple, required=False,
            queryset=self.project.values.filter(snapshot=None)
                                        .filter(value_type=VALUE_TYPE_FILE)
                                        .order_by('file'),
            to_field_name='id'
        )
        self.fields['attachments_snapshot'] = self.AttachmentSnapshotField(
            label=_('Snapshot'), widget=forms.RadioSelect, required=False,
            queryset=self.project.snapshots.all(), empty_label=_('Current')
        )
        self.fields['attachments_format'] = forms.ChoiceField(
            label=_('Format'), widget=forms.RadioSelect, required=False,
            choices=settings.EXPORT_FORMATS
        )

    def clean(self):
        cleaned_data = super().clean()

        if cleaned_data.get('attachments_answers') or cleaned_data.get('attachments_views'):
            if not cleaned_data.get('attachments_format'):
                self.add_error('attachments_format', _('This field is required.'))


class IssueMailForm(forms.Form):

    if settings.EMAIL_RECIPIENTS_CHOICES:
        recipients = forms.MultipleChoiceField(label=_('Recipients'), widget=forms.CheckboxSelectMultiple,
                                               required=not settings.EMAIL_RECIPIENTS_INPUT,
                                               choices=settings.EMAIL_RECIPIENTS_CHOICES)

    if settings.EMAIL_RECIPIENTS_INPUT:
        recipients_input = forms.CharField(label=_('Recipients'), widget=forms.Textarea(attrs={
            'placeholder': _('Enter recipients line by line')
        }), required=not settings.EMAIL_RECIPIENTS_CHOICES)

    def clean(self):
        cleaned_data = super().clean()

        if settings.EMAIL_RECIPIENTS_INPUT and \
                cleaned_data.get('recipients') == [] and \
                cleaned_data.get('recipients_input') == []:
            self.add_error('recipients_input', _('This field is required.'))

    def clean_recipients_input(self):
        email_validator = EmailValidator()
        cleaned_data = []

        for line in self.cleaned_data['recipients_input'].splitlines():
            email = line.strip()
            email_validator(email)
            cleaned_data.append(email)

        return cleaned_data


class UploadFileForm(forms.Form):
    uploaded_file = forms.FileField(
        label='Select a file',
    )
