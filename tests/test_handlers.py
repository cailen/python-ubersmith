import json

from mock import Mock, patch
import pytest
from six import text_type

from ubersmith.api import HttpRequestHandler, METHODS
from ubersmith.exceptions import ResponseError, UpdatingTokenResponse


class DescribeHttpRequestHandler:
    test_data = 'this is some data'

    @pytest.fixture
    def response(self):
        response = Mock()
        response.headers = {
            'status': '200',
            'content-type': 'application/json',
        }
        response.content = json.dumps({
            'status': True,
            'error_code': None,
            'error_message': '',
            'data': self.test_data,
        })
        response.text = text_type(response.content)
        return response

    @pytest.fixture
    def bad_header_response(self):
        response = Mock()
        response.headers = {
            'status': '200',
            'content-type': 'text/html',
        }
        response.content = json.dumps({
            'status': True,
            'error_code': None,
            'error_message': '',
            'data': self.test_data,
        })
        response.text = text_type(response.content)
        return response

    @pytest.fixture
    def token_response(self):
        response = Mock()
        response.headers = {
            'status': '200',
            'content-type': 'text/html',
        }
        response.content = '\n<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">\n<html>\n<head>\n\t<title>Updating Token...</title>\n\t<link rel="shortcut icon" type="image/x-icon" href="/ubericon.ico">\n\t<meta http-equiv="Refresh" content="4">\n\t<link href="/locale/en_US/css/stylesheet.css" rel="stylesheet" type="text/css">\n\t<style type="text/css">\n\t<!--\n.config-box-4 {height:auto !important;height:400px;min-height:400px;}\n\t-->\n\t</style>\n\t<script type="text/javascript" src="/js/jquery.js"></script>\n\t<script language="javascript">\n\t\tif (top.location != location) {\n\t\t\ttop.location.href = document.location.href;\n\t\t}\n\t\t$(function() {\t\n\t\t\t$("body").delegate("div.notification a.close","click",function(e) {\n\t\t\t\te.preventDefault();\n\t\t\t\t$(this).closest(\'div.notification-wrapper\').hide();\n\t\t\t});\n\t\t});\n\t\t\n\t</script>\n</head>\n<body>\n\t<div style="background: #ccccff url(\'/images/background_pagebar.png\') repeat-x top left;padding:0 10px;border-bottom:1px solid #999999;">\n\t\t<div style="padding:6px 0;">\n\t\t\t<img src="/images/logo_ubersmith.png" width="126" height="24" border="0" />\n\t\t</div>\n\t</div>\n\t\n\t<div class="config-box-1" style="margin:15px;"><div class="config-box-2"><div class="config-box-3"><div class="config-box-4">\n<table border="0" cellpadding="10" cellspacing="0">\n\t\t\t\t\t<tr valign="top">\n\t\t\t\t\t\t<td rowspan="2"><img src="/images/uber-anim.gif" /></td>\n\t\t\t\t\t\t<td class="CellText"><span style="font-size:150%;font-weight:bold;">Ubersmith Token Update</span></td>\n\t\t\t\t\t</tr>\n\t\t\t\t\t<tr>\n\t\t\t\t\t\t<td class="CellText">Please wait while your token is updated.</td>\n\t\t\t\t\t</tr>\n\t\t\t\t</table>\n\t</div></div></div></div>\n</body>\n</html>\n'
        response.text = text_type(response.content)
        return response

    def it_handles_normal_responses(self, response):
        h = HttpRequestHandler('')
        h._send_request = Mock(return_value=response)
        assert self.test_data == h.process_request('uber.method_list')

    def it_raises_response_error(self, bad_header_response):
        h = HttpRequestHandler('')
        h._send_request = Mock(return_value=bad_header_response)
        with pytest.raises(ResponseError):
            h.process_request('uber.method_list')

    def it_handles_updating_token(self, response, token_response):
        returns = [
            token_response,
            token_response,
            response,
        ]
        h = HttpRequestHandler('')
        h._send_request = Mock(side_effect=lambda *args: returns.pop(0))
        with patch('ubersmith.api.time') as time:
            time.sleep = lambda x: None
            assert self.test_data == h.process_request('uber.method_list')

    def it_raises_updating_token_after_3_tries(self, response, token_response):
        returns = [
            token_response,
            token_response,
            token_response,
            response,
        ]
        h = HttpRequestHandler('')
        h._send_request = Mock(side_effect=lambda *args: returns.pop(0))
        with patch('ubersmith.api.time') as time:
            time.sleep = lambda x: None
            with pytest.raises(UpdatingTokenResponse):
                h.process_request('uber.method_list')

    def it_is_able_to_proxy_calls_to_modules(self):
        h = HttpRequestHandler('')
        for call_base, call_name in (m.split('.') for m in METHODS):
            assert hasattr(h, call_base)
            proxy = getattr(h, call_base)
            partial = getattr(proxy, call_name)
            assert callable(partial)
            assert partial.keywords.get('request_handler') == h
