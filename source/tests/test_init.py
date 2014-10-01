# coding=utf-8
import unittest
import mock

from source.lib import to_unicode, get_counters, fix_market_url, PREFIX_GOOGLE_MARKET, prepare_url, get_url, ERROR_REDIRECT, make_pycurl_request, REDIRECT_HTTP, MARKET_SCHEME, REDIRECT_META,to_str, \
    get_redirect_history

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
        self.assertEquals(get_url(url, timeout=10), (url, ERROR_REDIRECT, None))

    def test_get_url_ok_redirect(self):
        """
        ignoring ok login redirects
        :return:
        """
        url = "some url"
        new_redirect_url = 'http://odnoklassniki.ru/asdasd.st.redirect'
        content = 'this is the end'
        with mock.patch('source.lib.make_pycurl_request', mock.Mock(return_value=(content, new_redirect_url))):
            self.assertEquals(get_url(url, timeout=10), (None, None, content))

    # def test_get_url_another_redirect(self):
    #     new_redirect_url = 'another redirect url'
    #     content = 'this is the end'
    #     prepare_url_return = 'prepare_url'
    #     with mock.patch('source.lib.make_pycurl_request', mock.Mock(return_value=(content, new_redirect_url))),\
    #         mock.patch('source.lib.prepare_url', mock.Mock(return_value=prepare_url_return)) as prepare_url, \
    #         mock.patch('source.lib.urlsplit', mock.Mock()):
    #             self.assertEquals(get_url(new_redirect_url, timeout=10), (prepare_url_return, REDIRECT_HTTP, content))
    #             prepare_url.assert_called_once_with(new_redirect_url)
    #             fix_market_url.assert_called_once_with(new_redirect_url)

    def test_get_url_market_url_http_redirect_type(self):
        with mock.patch('source.lib.fix_market_url', mock.Mock()) as fix_market_url:
            new_redirect_url = "market://market.url"
            prepare_url_return = 'url after prepare'
            content = 'this is original content'
            with mock.patch('source.lib.make_pycurl_request', mock.Mock(return_value=(content, new_redirect_url))):
                with mock.patch('source.lib.prepare_url', mock.Mock(return_value=prepare_url_return)) as prepare_url:
                     self.assertEquals(get_url(new_redirect_url, timeout=10), (prepare_url_return, REDIRECT_HTTP, content))
                     fix_market_url.assert_called_once_with(new_redirect_url)

    def test_get_url_none_redirect_url_none_redirect_type(self):
        """
        redirect url is none
        return null redirect type
        :return:
        """
        with mock.patch('source.lib.fix_market_url', mock.Mock()) as fix_market_url:
            new_redirect_url = None
            prepare_url_return = None
            content = 'this is original content'
            with mock.patch('source.lib.make_pycurl_request', mock.Mock(return_value=(content, new_redirect_url))):
                with mock.patch('source.lib.check_for_meta', mock.Mock(return_value=None)):
                    with mock.patch('source.lib.prepare_url', mock.Mock(return_value=prepare_url_return)) as prepare_url:
                        self.assertEquals((prepare_url_return, None, content), get_url('some url', timeout=10))
                        assert not fix_market_url.called
                        prepare_url.assert_called_once_with(new_redirect_url)

    def test_get_url_none_redirect_url_meta_redirect_type(self):
        """
        redirect url is none при make_pycurl_request
        return meta redirect type
        :return:
        """
        with mock.patch('source.lib.fix_market_url', mock.Mock()) as fix_market_url:
            prepare_url_return = new_redirect_url = "not none redirect url"
            content = 'this is original content'
            with mock.patch('source.lib.make_pycurl_request', mock.Mock(return_value=(content, None))):
                with mock.patch('source.lib.check_for_meta', mock.Mock(return_value=new_redirect_url)):
                    with mock.patch('source.lib.prepare_url', mock.Mock(return_value=prepare_url_return)) as prepare_url:
                        self.assertEquals((prepare_url_return, REDIRECT_META, content), get_url('some url', timeout=10))
                        assert not fix_market_url.called
                        prepare_url.assert_called_once_with(new_redirect_url)

    def test_init_to_unicode_with_unicode_str(self):
        """
        Сразу передаем UNICODE
        :return:
        """
        val = u'unicode'
        result = to_unicode(val)
        is_unicode = isinstance(result, unicode)
        assert is_unicode is True

    def test_init_to_unicode_with_not_unicode_str(self):
        """
        Передаем ASCII
        :return:
        """
        val = 'ascii'
        result = to_unicode(val)
        is_unicode = isinstance(result, unicode)
        assert is_unicode is True

    def test_init_to_str_with_ascii(self):
        """
        Передаем ASCII
        :return:
        """
        val = 'ascii'
        result = to_str(val)
        is_str = isinstance(result, str)
        assert is_str is True

    def test_init_to_str_with_unicode(self):
        """
        Передаем UNICODE
        :return:
        """
        val = u'unicode'
        result = to_str(val)
        is_str = isinstance(result, str)
        assert is_str is True

    def test_get_redirect_history_mm_ok_domains(self):
        """
        правильные возвращаемые значения для одноклассников и mm
        :return:
        """
        ok_url = 'https://odnoklassniki.ru/'
        mm_url = 'https://my.mail.ru/apps/'
        history_types = []
        counters = []
        self.assertEquals((history_types, [ok_url], counters), get_redirect_history(url=ok_url, timeout=1), "non valid return for ok url")
        self.assertEquals((history_types, [mm_url], counters), get_redirect_history(url=mm_url, timeout=1), "non valid return for mm url")

    def test_get_redirect_history_none_redirect_url_none_counters(self):
        """
        правильные возвращаемые значения для redirect_url = none и отсутствии контента
        :return:
        """
        url = "http://url.ru"
        redirect_url = None
        redirect_type = None
        content = None
        history_types = []
        history_urls = [url]
        counters = []
        with mock.patch('source.lib.get_url', mock.Mock(return_value=(redirect_url, redirect_type, content))):
            self.assertEquals((history_types, history_urls, counters), get_redirect_history(url=url, timeout=1), "non valid return values")

    def test_get_redirect_history_error_redirect_type(self):
        url = "http://url.ru"
        redirect_url = "http://redirect.url"
        redirect_type = ERROR_REDIRECT
        content = 'google-analytics.com/ga.js'
        google_counter = "GOOGLE_ANALYTICS"
        history_types = [redirect_type]
        history_urls = [url, redirect_url]
        counters = [google_counter]
        with mock.patch('source.lib.get_url', mock.Mock(return_value=(redirect_url, redirect_type, content))):
            self.assertEquals((history_types, history_urls, counters), get_redirect_history(url=url, timeout=1), "non valid return values")


    def test_max_redirect_break(self):
        """
        тест что был произведен только 1 редирект
        :return:
        """
        url = "http://url.ru"
        redirect_url = "http://redirect.url"
        redirect_type = "good redirect"
        content = None
        history_types = [redirect_type]
        history_urls = [url, redirect_url]
        counters = []
        with mock.patch('source.lib.get_url', mock.Mock(return_value=(redirect_url, redirect_type, content))):
            self.assertEquals((history_types, history_urls, counters), get_redirect_history(url=url, timeout=1, max_redirects=1), "non valid return values")

    def test_max_redirect_break(self):
        """
        тест что был произведен только 1 редирект
        :return:
        """
        url = "http://url.ru"
        redirect_url = "http://redirect.url"
        redirect_type = "good redirect"
        content = None
        history_types = [redirect_type]
        history_urls = [url, redirect_url]
        counters = []
        with mock.patch('source.lib.get_url', mock.Mock(return_value=(redirect_url, redirect_type, content))):
            self.assertEquals((history_types, history_urls, counters), get_redirect_history(url=url, timeout=1, max_redirects=1), "non valid return values")


pass