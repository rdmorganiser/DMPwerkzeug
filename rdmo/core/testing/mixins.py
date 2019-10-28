import logging
import os

from io import StringIO

from django.conf import settings
from django.core.management import call_command
from django.urls import reverse

from test_generator.core import TestMixin

from rdmo.core.utils import get_languages
from rdmo.core.testing.utils import (
    fuzzy_compare,
    get_super_client,
    read_xml_file,
    sanitize_xml
)

logger = logging.getLogger(__name__)


class TestTranslationMixin(object):

    def get_instance_as_dict(self, instance):
        model_data = super(TestTranslationMixin, self).get_instance_as_dict(instance)

        for lang_code, lang_string, lang_field in get_languages():
            for field in self.trans_fields:
                model_field = '%s_%s' % (field, lang_field)
                data_field = '%s_%s' % (field, lang_code)
                model_data[data_field] = model_data.get(model_field)

        return model_data


class TestExportViewMixin(TestMixin):

    export_formats = ('xml', 'html', 'rtf')

    def _test_export_list(self, username):

        for format in self.export_formats:
            url = reverse(self.url_names['export_view'], kwargs={'format': format})
            response = self.client.get(url)

            try:
                self.assertEqual(response.status_code, self.status_map['export_view'][username])
            except AssertionError:
                print(
                    ('test', 'test_export'),
                    ('username', username),
                    ('url', url),
                    ('format', format),
                    ('status_code', response.status_code),
                    ('content', response.content)
                )
                raise


class TestImportViewMixin(TestMixin):

    import_formats = ('xml', )

    def _test_import_get(self, username):

        for format in self.import_formats:
            url = reverse(self.url_names['import_view'], kwargs={'format': format})
            response = self.client.get(url)

            try:
                self.assertEqual(response.status_code, self.status_map['import_view'][username])

                if response.status_code == 302:
                    if username == 'anonymous':
                        self.assertRedirects(response, reverse('account_login') + '?next=' + url)
                    else:
                        self.assertRedirects(response, reverse(self.url_names['list_view']))

            except AssertionError:
                print(
                    ('test', 'test_import'),
                    ('username', username),
                    ('url', url),
                    ('status_code', response.status_code),
                    ('content', response.content)
                )
                raise

    def _test_import_post(self, username):

        for format in self.import_formats:

            url = reverse(self.url_names['import_view'], kwargs={'format': format})

            with open(self.import_file, encoding='utf8') as f:
                response = self.client.post(url, {'attachment': f})

            try:
                self.assertEqual(response.status_code, self.status_map['import_view'][username])
            except AssertionError:
                print(
                    ('test', 'test_import'),
                    ('username', username),
                    ('url', url),
                    ('status_code', response.status_code),
                    ('content', response.content)
                )
                raise


class TestImportManageMixin(TestMixin):

    def test_runner(self):
        logfile = settings.LOGGING_DIR + 'rdmo.log'
        self.import_test(logfile)
        self.assert_logfile(logfile)
        self.assert_export_data()
        self.check_export_apis()

    def import_test(self, logfile):
        logger.debug('Importing %s', self.import_file)

        out, err = StringIO(), StringIO()

        if os.path.isfile(logfile):
            open(logfile, 'w').close()

        try:
            call_command('import', self.import_file, '--user=%s' % self.import_user, stdout=out, stderr=err)
        except AttributeError:
            call_command('import', self.import_file, stdout=out, stderr=err)

        self.assertFalse(out.getvalue())
        self.assertFalse(err.getvalue())

    def assert_logfile(self, logfile):
        if os.path.isfile(logfile):
            logger.debug('Looking for errors in the log file')

            successful = True
            with open(logfile, 'r') as fh:
                lines = fh.read().splitlines()
            for l in lines:
                if '[ERROR]' in l:
                    logger.debug(l)
                    successful = False
            if successful is True:
                logger.debug('Logs are clean')
            else:
                logger.debug('Errors found in log file')
                self.assertFalse('Found error messages in logfile.')

    def assert_export_data(self):
        if self.compare_import_to_export_data is True:
            logger.debug('Comparing import to export for %s', self.export_api)
            client = get_super_client()
            response = client.get(reverse(self.export_api, kwargs=self.export_api_kwargs))
            exported_xml_data = sanitize_xml(response.content)
            imported_xml_data = read_xml_file(self.import_file)

            successful = fuzzy_compare(imported_xml_data, exported_xml_data, self.compare_import_to_export_ignore_list)
            if successful is False:
                self.assertFalse('Export data differ from import data')
            if successful is True:
                logger.debug('Compare successful')
            else:
                logger.debug('Compare failed')

    def check_export_apis(self):
        try:
            self.export_api_format_list
        except AttributeError:
            pass
        else:
            logger.debug('Testing export apis of %s', self.export_api)

            successful = True
            client = get_super_client()
            for format in self.export_api_format_list:
                kwargs = {}
                kwargs['format'] = format
                try:
                    self.export_api_kwargs['pk']
                except KeyError:
                    pass
                else:
                    kwargs['pk'] = self.export_api_kwargs['pk']

                url = reverse(self.export_api, kwargs=kwargs)
                response = client.get(url)

                if response.status_code == 200:
                    logger.debug('Successful request %s %s', url, response.status_code)
                else:
                    logger.debug('Failed request %s %s', url, response.status_code)
                    successful = False

            self.assertEqual(successful, True)
