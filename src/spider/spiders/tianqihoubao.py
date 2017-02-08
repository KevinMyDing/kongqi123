# -*- coding: utf-8 -*-
import scrapy
import json
import chardet
from scrapy.exceptions import CloseSpider
from scrapy.http import HtmlResponse

from spider.items import WeatherCityItem, WeatherDayItem


class WeatherSpider(scrapy.Spider):
    name = "tianqihoubao"
    allowed_domains = ["tianqihoubao.com"]
    start_urls = [
        "http://www.tianqihoubao.com/lishi/"
    ]
    custom_settings = dict(
        DOWNLOAD_DELAY=2,
        CONCURRENT_REQUESTS_PER_DOMAIN=8,
        CONCURRENT_REQUESTS_PER_IP=8,
        DEFAULT_REQUEST_HEADERS={
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate, sdch",
            "Accept-Language": "zh-CN,zh;q=0.8,zh-TW;q=0.6,en-US;q=0.4,en;q=0.2",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Cookie": "bdshare_firstime=1486523907895; ASP.NET_SessionId=z5j1rq5530iqum2xsqqwh2zn",
            "Host": "www.tianqihoubao.com",
            "Pragma": "no-cache",
            "Referer": "http://www.tianqihoubao.com/weather/province.aspx?id=340000",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36",
        },
        DOWNLOADER_MIDDLEWARES={
            'spider.middlewares.SpiderTianQiHouBaoMiddleware': 1000,
        },
        ITEM_PIPELINES={
            'spider.pipelines.CitiesPipeline': 300,
        }
    )

    def __init__(self, *args, **kwargs):
        super(WeatherSpider, self).__init__(*args, **kwargs)

    def parse(self, response):
        city_list = response.xpath('//div[@class="citychk"]//dd[1]/a')
        # print "city_list: %s" % str(city_list)
        # raise CloseSpider('test')
        # print response.body_as_unicode()

        for city in city_list:
            city_name = city.xpath('text()').extract()
            city_url = city.xpath('@href').extract()

            city_name = city_name[0]  # .encode('utf-8')
            city_url = city_url[0]  # .encode('utf-8')

            item = WeatherCityItem()
            item['city_name'] = city_name.strip()
            item['city_url'] = city_url.strip()

            print u'----- WeatherCityItem:%s' % json.dumps(dict(item), indent=4)
            # yield item

            url = response.urljoin(city_url)
            meta = {'city_name': item['city_name']}
            yield scrapy.Request(url=url, meta=meta, callback=self.parse_month, priority=20)

    def parse_month(self, response):
        city_name = response.meta['city_name']
        month_list = response.xpath('//div[@id="content"]//li/a')
        if len(month_list) < 1:
            return

        for month in month_list:
            day_url = month.xpath('@href').extract_first(default='')
            url = response.urljoin(day_url)
            meta = {'city_name': city_name}

            print u'----- WeatherCityUrl:%s' % url
            yield scrapy.Request(url=url, meta=meta, callback=self.parse_day, priority=90)

    def parse_day(self, response):
        city_name = response.meta['city_name']
        day_list = response.xpath('//table//tr[position()>1]')
        if len(day_list) < 1:
            return

        for day in day_list:
            weather_date = day.xpath('.//td[1]/a/text()').extract_first(default='')
            weather_date = weather_date.replace(u'年', '-')
            weather_date = weather_date.replace(u'月', '-')
            weather_date = weather_date.replace(u'日', '')

            weather_am_pm = day.xpath('.//td[2]/text()').extract_first(default='')
            weather_am_pm = weather_am_pm.split('/')
            weather_am = '' if not weather_am_pm[0] else weather_am_pm[0]
            weather_pm = '' if not weather_am_pm[1] else weather_am_pm[1]

            weather_top_down = day.xpath('.//td[3]/text()').extract_first(default='')
            weather_top_down = weather_top_down.split('/')
            weather_top = '' if not weather_top_down[0] else weather_top_down[0]
            weather_down = '' if not weather_top_down[1] else weather_top_down[1]

            weather_wind = day.xpath('.//td[4]/text()').extract_first(default='')
            weather_wind = weather_wind.split('/')
            print u"weather_wind: %s" % str(weather_wind)

            weather_am_wind = '' if not weather_wind[0] else weather_wind[0].strip()
            weather_pm_wind = '' if not weather_wind[1] else weather_wind[1].strip()
            print u"weather_am_wind: %s" % weather_am_wind
            print u"weather_pm_wind: %s" % weather_pm_wind

            weather_am_wind = weather_am_wind.split(' ')
            weather_am_wind_type = '' if not weather_am_wind[0] else weather_am_wind[0]
            weather_am_wind_level = '' if not weather_am_wind[1] else weather_am_wind[1]

            weather_pm_wind = weather_pm_wind.split(' ')
            weather_pm_wind_type = '' if not weather_pm_wind[0] else weather_pm_wind[0]
            weather_pm_wind_level = '' if not weather_pm_wind[1] else weather_pm_wind[1]

            item = WeatherDayItem()
            '''
            weather_date: 2017-02-01
            city_name: 通辽
            weather_am: 晴
            weather_pm: 晴
            weather_top: -2℃
            weather_down: -9℃
            weather_am_wind_type: 西北风
            weather_am_wind_level: 3-4级
            weather_pm_wind_type: 西风
            weather_pm_wind_level: 3-4级
            '''
            print u"weather_date: %s" % weather_date.strip()
            print u"city_name: %s" % city_name  # .decode('utf-8'), type(city_name)
            print u"weather_am: %s" % weather_am.strip()
            print u"weather_pm: %s" % weather_pm.strip()
            print u"weather_top: %s" % weather_top.strip()
            print u"weather_down: %s" % weather_down.strip()
            print u"weather_am_wind_type: %s" % weather_am_wind_type.strip()
            print u"weather_am_wind_level: %s" % weather_am_wind_level.strip()
            print u"weather_pm_wind_type: %s" % weather_pm_wind_type.strip()
            print u"weather_pm_wind_level: %s" % weather_pm_wind_level.strip()

            raise CloseSpider('test')

            item['weather_date'] = weather_date.strip()
            item['city_id'] = 0
            item['city_name'] = city_name.strip()
            item['weather_am'] = weather_am.strip()
            item['weather_pm'] = weather_pm.strip()
            item['weather_top'] = (weather_top.strip())
            item['weather_down'] = (weather_down.strip())
            item['weather_am_wind_type'] = weather_am_wind_type.strip()
            item['weather_am_wind_level'] = weather_am_wind_level.strip()
            item['weather_pm_wind_type'] = weather_pm_wind_type.strip()
            item['weather_pm_wind_level'] = weather_pm_wind_level.strip()

            # print u'----- WeatherItem:%s' % json.dumps(dict(item), indent=4)
            # yield item

