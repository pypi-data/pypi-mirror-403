import re
from lazyllm.thirdparty import httpx
import json
from lazyllm.module.module import ModuleBase
from lazyllm.tools.http_request.http_executor_response import HttpExecutorResponse

class HttpRequest(ModuleBase):
    """General HTTP request executor.

This class builds and sends HTTP requests with support for dynamic variable substitution, API key injection, JSON or form data encoding, and file-aware response parsing.

Args:
    method (str): HTTP method, such as 'GET', 'POST', etc.
    url (str): The target URL for the HTTP request.
    api_key (str): Optional API key, inserted into query parameters.
    headers (dict): HTTP request headers.
    params (dict): URL query parameters.
    body (Union[str, dict]): HTTP request body (raw string or JSON-formatted dict).
    timeout (int): Timeout duration for the request (in seconds).
    proxies (dict, optional): Proxy settings for the request, if needed.


Examples:
    >>> from lazyllm.components import HttpRequest
    >>> request = HttpRequest(
    ...     method="GET",
    ...     url="https://api.github.com/repos/openai/openai-python",
    ...     api_key="",
    ...     headers={"Accept": "application/json"},
    ...     params={},
    ...     body=None
    ... )
    >>> result = request()
    >>> print(result["status_code"])
    ... 200
    >>> print(result["content"][:100])
    ... '{"id":123456,"name":"openai-python", ...}'
    """
    def __init__(self, method, url, api_key, headers, params, body, timeout=10, proxies=None):
        super().__init__()
        if not url:
            return

        self._method = method
        self._url = url
        self._api_key = api_key
        self._headers = headers
        self._params = params
        self._body = body
        self._timeout = timeout
        self._proxies = proxies

    def _process_api_key(self, headers, params):
        if self._api_key and self._api_key != '':
            params = params or {}
            params['api_key'] = self._api_key
        return headers, params

    def forward(self, *args, **kwargs):
        def _map_input(target_str):
            if not isinstance(target_str, str):
                return target_str

            # TODO: replacements could be more complex to create.
            replacements = {**kwargs, **(args[0] if args and isinstance(args[0], dict) else {})}
            if not replacements:
                return target_str

            pattern = r'\{\{([^}]+)\}\}'

            full_match = re.fullmatch(pattern, target_str)
            if full_match:
                key = full_match.group(1)
                if key in replacements:
                    return replacements[key]

            def replacer(m):
                key = m.group(1)
                if key not in replacements:
                    return m.group(0)  # Keep original if no replacement found
                replacement = replacements[key]
                if isinstance(replacement, (dict, list, bool)) or replacement is None:
                    return json.dumps(replacement, ensure_ascii=False)
                return str(replacement)

            return re.sub(pattern, replacer, target_str)

        url = _map_input(self._url)
        params = {key: _map_input(value) for key, value in self._params.items()} if self._params else None
        headers = {key: _map_input(value) for key, value in self._headers.items()} if self._headers else None
        headers, params = self._process_api_key(headers, params)
        if isinstance(headers, dict) and headers.get('Content-Type') == 'application/json':
            try:
                body = json.dumps(self._body) if isinstance(self._body, dict) else self._body
                body = json.loads(_map_input(body))

                http_response = httpx.request(method=self._method, url=url, headers=headers,
                                              params=params, json=body, timeout=self._timeout,
                                              proxies=self._proxies)
            except json.JSONDecodeError:
                raise ValueError(f'Invalid JSON format: {self._body}')
        else:
            body = (json.dumps({k: _map_input(v) for k, v in self._body.items()})
                    if isinstance(self._body, dict) else _map_input(self._body))

            http_response = httpx.request(method=self._method, url=url, headers=headers,
                                          params=params, data=body, timeout=self._timeout,
                                          proxies=self._proxies)

        response = HttpExecutorResponse(http_response)

        _, file_binary = response.extract_file()

        outputs = {
            'status_code': response.status_code,
            'content': response.content if len(file_binary) == 0 else None,
            'headers': response.headers,
            'file': file_binary
        }
        return outputs
