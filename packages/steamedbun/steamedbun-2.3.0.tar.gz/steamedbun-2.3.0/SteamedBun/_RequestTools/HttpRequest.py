"""
@Author: 馒头 (chocolate)
@Email: neihanshenshou@163.com
@File: HttpRequest.py
@Time: 2023/12/9 18:00
"""

import json as json_v2
from urllib import parse
from urllib.parse import unquote

from requests import Response
from requests import Session

from SteamedBun import logger


def create_response_hook(other: str = "traceid"):
    """
    闭包函数：创建带自定义参数的响应钩子
    :param other: 响应头中TraceId的字段名
    :return: 真正的钩子函数
    """

    def __hook_response(response: Response, **kwargs):

        response.encoding = "utf-8"

        try:
            result = json_v2.dumps(response.json(), ensure_ascii=False)
        except Exception as e:
            result = response.text or e

        kwargs = {"服务code码": response.status_code, **kwargs}
        if kwargs.get("proxies"):
            del kwargs["proxies"]

        query = unquote(parse.urlparse(response.url).query or parse.urlparse(response.url).params)
        body = response.request.body
        other_value = response.headers.get(other, "未获取到对应值")
        try:
            body = body.decode(encoding="utf-8") if body else None
            body = json_v2.dumps(json_v2.loads(body), ensure_ascii=False)
        except Exception as e:
            print("" and e, end="")

        logger.info(f"""
        请求方法: {response.request.method}
        请求地址: {response.request.url.split("?")[0]}
        请求内容: {body or query or {} }
        请求响应: {result}
        请求时长: {response.elapsed.total_seconds()} 秒
        更多内容: {kwargs}
        {other}: {other_value}
            """)

    return __hook_response


def request(url,
            method="post",
            show=True,
            params=None,
            data=None,
            headers=None,
            cookies=None,
            timeout=10,
            verify=None,
            json=None,
            other: str = "traceid",
            **kwargs):
    """

    :param url:
    :param method:
    :param show:
    :param params:
    :param data:
    :param headers:
    :param cookies:
    :param timeout:
    :param verify:
    :param json:
    :param other:
    :param kwargs:
    :return:
    """

    with Session() as session:
        hooks = None
        if show:
            # 调用闭包，传入other，得到带参数的钩子函数
            hook_func = create_response_hook(other=other)
            hooks = {"response": hook_func}

        return session.request(
            method=method,
            url=url,
            params=params,
            data=data,
            headers=headers,
            cookies=cookies,
            timeout=timeout,
            verify=verify,
            json=json,
            hooks=hooks,
            **kwargs)
