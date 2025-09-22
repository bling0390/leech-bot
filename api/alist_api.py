# -*- coding: UTF-8 -*-
from typing import Literal

import httpx
from httpx import Response

from config.config import ALIST_HOST, ALIST_TOKEN


class AListAPI:
    @staticmethod
    async def _send_request(
        method: Literal["GET", "POST", "PUT"],
        url,
        headers=None,
        json=None,
        params=None,
        data=None,
        timeout=10,
    ):
        async with httpx.AsyncClient() as client:
            if method == "GET":
                response = await client.get(
                    url, headers=headers, params=params, timeout=timeout
                )
            elif method == "POST":
                response = await client.post(
                    url, headers=headers, json=json, timeout=timeout
                )
            elif method == "PUT":
                response = await client.put(
                    url, headers=headers, data=data, timeout=timeout
                )
            response.raise_for_status()

            data = response.json()

            if data['code'] == 401:
                raise Exception('401 Unauthorized')

            return data


    # 获取存储列表
    @staticmethod
    async def get_storages():
        return await AListAPI._send_request(
            'GET',
            f'{ALIST_HOST}/api/admin/storage/list',
            headers={
                'Authorization': ALIST_TOKEN
            }
        )
