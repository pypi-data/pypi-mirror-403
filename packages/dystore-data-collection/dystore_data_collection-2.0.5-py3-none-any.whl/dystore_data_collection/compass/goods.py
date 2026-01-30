"""
电商罗盘-商品
"""

from collections.abc import Callable
from random import uniform
from time import sleep

from BrowserAutomationLauncher import Browser, DataPacketProcessor
from BrowserAutomationLauncher._utils.tools import DateTimeTools
from DrissionPage._pages.mix_tab import MixTab
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

from ._utils import pick__daterange


class Urls:
    goods_detail = (
        'https://compass.jinritemai.com/shop/product-detail?product_id={goods_id}'
    )


class DataPacketUrls:
    goods_detail = 'https://compass.jinritemai.com/compass_api/shop/product/product_detail/core_data/index_data'


class Goods:
    def __init__(self, browser: Browser):
        self._browser = browser

    def _wait__goods_detail_datapacket(
        self, page: MixTab, callback: Callable, timeout=30
    ):
        """等待商品详情数据包"""

        page.listen.start(
            targets=DataPacketUrls.goods_detail, method='GET', res_type='XHR'
        )
        callback()
        return page.listen.wait(timeout=timeout)

    def get__goods_detail(
        self, goods_id: str, date: str | list[str] | list[list[str]], close_page=True
    ):
        """
        获取指定商品详情

        Args:
            goods_id: 商品ID
            date: `日期|日期列表|日期范围列表`, 日期范围需要传入 `[[开始日期, 结束日期]]`
            close_page: 是否自动关闭页面
        Returns:
            日期数据对象: {日期: 数据对象}
        """

        url = Urls.goods_detail.format(goods_id=goods_id)
        page = self._browser.chromium.new_tab()
        entry_packet = self._wait__goods_detail_datapacket(page, lambda: page.get(url))
        if not entry_packet:
            raise TimeoutError('进入页面后获取商品详情数据包超时')
        entry_packet_data = DataPacketProcessor(entry_packet).filter('?msg')
        if 'msg' in entry_packet_data and '无权限' in entry_packet_data['msg']:
            sleep(5)

        date_range_list: list[list[str]] = []
        if isinstance(date, str):
            date_range_list.append([date, date])
        elif isinstance(date, list):
            if all(isinstance(item, list) for item in date):
                date_range_list = date
            else:
                date_range_list.extend([item, item] for item in date)
        else:
            raise TypeError('参数 date 类型错误')

        @retry(
            retry=retry_if_exception_type(ValueError),
            wait=wait_fixed(2),
            stop=stop_after_attempt(3),
        )
        def query_data(begin_date: str, end_date: str):
            is_yesterday = begin_date == end_date == DateTimeTools.date_yesterday()
            sleep(2)

            if is_yesterday:
                yesterday_btn = page.ele('近1天', timeout=3)
                datapacket = self._wait__goods_detail_datapacket(
                    page, lambda: yesterday_btn.click(by_js=True)
                )
            else:
                datapacket = self._wait__goods_detail_datapacket(
                    page, lambda: pick__daterange(page, begin_date, end_date)
                )

            if not datapacket:
                raise TimeoutError('修改日期后获取数据包超时')

            # 判断数据包的日期与设置的是否一致
            [begin_date_formated, end_date_formated] = [
                date.replace('-', '/') for date in [begin_date, end_date]
            ]
            search_params = datapacket.request.params
            if (
                not isinstance(search_params, dict)
                or begin_date_formated not in search_params.get('begin_date', '')
                or end_date_formated not in search_params.get('end_date', '')
            ):
                raise ValueError('数据包日期与设置的不一致')

            data = DataPacketProcessor(datapacket).filter(
                ['attributes', 'data[0].metrics']
            )

            titles = {
                item['index_name']: item['index_display'].strip()
                for item in data['attributes']
            }

            metrics = {}
            for key, data_dict in data['metrics'].items():
                if 'value' not in data_dict:
                    continue

                value_dict = data_dict['value']
                if not isinstance(value_dict, dict):
                    continue

                value = value_dict.get('value')
                unit = value_dict.get('unit')

                if unit == 'price' and isinstance(value, (int, float)):
                    value = value / 100

                metrics[key] = value

            return {name: metrics[key] for key, name in titles.items()}

        data_list: dict[str, dict] = {}
        for date_range in date_range_list:
            if not isinstance(date_range, list) or len(date_range) != 2:
                continue

            try:
                begin_date, end_date = date_range
                data = query_data(begin_date=begin_date, end_date=end_date)
                data_list[begin_date] = data
            except Exception as err:
                print(f'[{begin_date}~{end_date}] 商品详情数据获取出错: {err}')

            sleep(uniform(1, 1.5))

        if close_page is True:
            page.close()

        return data_list
