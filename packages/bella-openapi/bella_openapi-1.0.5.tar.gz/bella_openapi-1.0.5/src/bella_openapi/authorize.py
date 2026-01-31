import httpx
import logging
from .config import openapi_config
from .exception import AuthorizationException
from .schema import ApikeyInfo


def check_configuration() -> bool:
    res = openapi_config.OPENAPI_HOST is not None
    return res


def validate_token(token: str) -> str:
    """
    根据传入token， 解析用户身份
    :param token:
    :return: 用户身份，返回userId
    :raises: AuthorizationException 如果token无效， 抛出异常
    """
    apikey_info = whoami(token)
    if apikey_info.user_id is not None:
        return str(apikey_info.user_id)
    else:
        raise AuthorizationException("userId not found in whoami response", 401)


def support_model(token: str, model: str) -> bool:
    """
    根据传入token，判断用户是否有对应的模型权限
    :param token: 用户token
    :param model: 模型名
    :return: bool
    """
    url = openapi_config.OPENAPI_HOST + "/v1/openapi/support/model"
    # 使用httpx发送get请求
    response = httpx.get(url, headers={"Authorization": token}, params={"model": model})
    if response.status_code == 200:
        return response.json()['data']
    else:
        raise AuthorizationException(response.text, response.status_code)



def whoami(token: str) -> ApikeyInfo:
    """
    调用whoami接口获取用户apikey信息
    :param token:
    :return: ApikeyInfo对象
    :raises: AuthorizationException 如果token无效，抛出异常
    """
    url = openapi_config.OPENAPI_HOST + "/v1/apikey/whoami"
    response = httpx.get(url, headers={"Authorization": token})
    if response.status_code == 200:
        result = response.json()
        if result.get('code') == 200:
            return ApikeyInfo(**result.get('data', {}))
        else:
            raise AuthorizationException(result.get('message', 'Unknown error'), response.status_code)
    else:
        raise AuthorizationException(response.text, response.status_code)


def validate_token_by_whoami(token: str) -> bool:
    """
    根据传入token， 通过whoami接口判断用户身份是否真的存在
    :param token:
    :return: bool, 如果用户身份存在，返回True，否则返回False
    """
    try:
        apikey_info = whoami(token)
        return apikey_info.user_id is not None
    except:
        return False
