# coding=utf-8
import unittest
import mock
import source

from source.lib import to_unicode, get_counters, fix_market_url, PREFIX_GOOGLE_MARKET, prepare_url, get_url, \
    ERROR_REDIRECT, make_pycurl_request

__author__ = 'maxim'


class InitTestCase(unittest.TestCase):

    def test_to_unicode_decoding(self):
        val = 'unicode str'
        to_unicode(val)


    def test_get_counters_without_counters(self):
        """
        в контенте нет ссылок на счетчики
        :return:
        """
        assert get_counters("content without counters") == []

    def test_get_counters_with_counters(self):
        """
        в контенте есть ссылки на счетчики
        :return:
        """
        google_analitics = 'GOOGLE_ANALYTICS'
        google_analitics_content = 'google-analytics.com/ga.js'
        ya_metrika = 'YA_METRICA'
        ya_metrika_content = 'mc.yandex.ru/metrika/watch.js'
        counter = [google_analitics, ya_metrika]
        self.assertEquals(get_counters(google_analitics_content + ya_metrika_content), counter)

    def test_fix_market_url(self):
        """
        преобразование ссылки на маркет
        :return:
        """
        market = "details?id=com.google.android.gm"
        market_url = PREFIX_GOOGLE_MARKET + market
        self.assertEquals(fix_market_url('market://' + market), market_url)

    def test_prepare_url_none(self):
        """
        url = None
        :return:
        """
        url = None
        assert prepare_url(url) == url

    def test_prepare_url_without_exception(self):
        """
        при кодировании в idna не вылетает exception
        :return:
        """
        my_mock = mock.MagicMock()
        with mock.patch('source.lib.urlparse', mock.Mock(return_value=[my_mock] * 6)),\
                mock.patch('source.lib.logger', mock.MagicMock()) as logger:
            prepare_url('url')
            my_mock.encode.assert_called_once()
            assert not logger.error.called

    def test_prepare_url_with_exception(self):
        """
        при кодировании в idna вылетает exception
        :return:
        """
        my_mock = mock.MagicMock()
        my_mock.encode.side_effect = UnicodeError("unicode error")
        with mock.patch('source.lib.urlparse', mock.Mock(return_value=[my_mock] * 6)),\
                mock.patch('source.lib.logger', mock.MagicMock()) as logger:
            prepare_url('url')
            assert logger.error.called

    @mock.patch('source.lib.prepare_url', mock.Mock())
    def test_pycurl_request_without_uagent_without_redirect_url(self):
        """
        не передается user_agent, redirect_url = None
        :return:
        """
        content = "this is original content"
        my_curl = mock.Mock()
        buffer = mock.Mock()
        with mock.patch('source.lib.pycurl.Curl', mock.Mock(return_value=my_curl)),\
        mock.patch('source.lib.to_unicode', mock.Mock()) as to_unicode,\
        mock.patch('source.lib.StringIO', mock.Mock(return_value=buffer)):
            buffer.getvalue.return_value = content
            my_curl.getinfo.return_value = None
            self.assertEquals(make_pycurl_request(url="url", timeout=10), (content, None))
            assert not mock.call(my_curl.USERAGENT, None) in my_curl.setopt.call_args_list
            assert not to_unicode.called


    @mock.patch('source.lib.prepare_url', mock.Mock())
    def test_pycurl_request_with_uagent_with_redirect_url(self):
        """
        не передается user_agent, redirect_url = None
        :return:
        """
        user_agent = "AGENT"
        content = "this is original content"
        redirect_url = "redirect.ru"
        my_curl = mock.Mock()
        buffer = mock.Mock()
        with mock.patch('source.lib.pycurl.Curl', mock.Mock(return_value=my_curl)),\
        mock.patch('source.lib.to_unicode', mock.Mock(return_value=redirect_url)) as to_unicode,\
        mock.patch('source.lib.StringIO', mock.Mock(return_value=buffer)):
            buffer.getvalue.return_value = content
            self.assertEquals(make_pycurl_request(url="url", timeout=10, useragent=user_agent), (content, redirect_url))
            my_curl.setopt.assert_any_call(my_curl.USERAGENT, user_agent)
            assert to_unicode.called

    @mock.patch('source.lib.make_pycurl_request', mock.Mock(side_effect=ValueError('value error')))
    def test_get_url_error_redirect(self):
        """
        get_url возвращает тип редиректа ERROR
        :return:
        """
        url = "some url"
        url, redirect_type, content = get_url(url, timeout=10)
        assert redirect_type == ERROR_REDIRECT and content is None
pass