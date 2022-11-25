import scrapy
from selenium import webdriver
from selenium.webdriver.common.by import By
from parsel import Selector
import logging
from selenium.webdriver.remote.remote_connection import LOGGER
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions


class PhonesSpiders(scrapy.Spider):
    name = 'phones'
    start_urls = [
        'https://ozon.ru/category/smartfony-15502/?sorting=rating',
    ]

    allowed_domains = ['ozon.ru']

    PRODUCT_URL = 'https://ozon.ru'
    MAX_SMARTPHONE = 100

    def __init__(self):
        options = webdriver.ChromeOptions()
        options.add_argument("headless")
        desired_capabilities = options.to_capabilities()
        self.driver = webdriver.Chrome(desired_capabilities=desired_capabilities)
        LOGGER.setLevel(logging.WARNING)
        self.true_count = 0
        super().__init__()

    def parse(self, response, **kwargs):
        all_products = response.xpath('//div[contains(@class,"widget-search-result-container")]//div[@class="k6r rk6"]')

        for product in all_products:
            product_title = product.xpath('.//a/span/span/text()').extract_first()
            short_characteristics = product.xpath('.//span[@class="dy9 yd9 zd2 tsBodyM"]/span//text()').extract()
            type_product = "|".join(short_characteristics)

            if 'Тип: |Смартфон|' in type_product or product_title.startswith('Смартфон'):
                href = product.xpath('.//a/@href').extract_first()
                smartphone_url = self.PRODUCT_URL + href
                yield scrapy.Request(smartphone_url, callback=self.parse_smartphone)
                # limit count of smartphones
                self.true_count += 1
                if self.true_count == self.MAX_SMARTPHONE:
                    return

        next_page = response.xpath('//a[@class="aa1m am1a"]/following-sibling::a[1]/@href').extract_first()
        if next_page is not None:
            next_page = response.urljoin(next_page)
            yield response.follow(next_page, callback=self.parse)

    def parse_smartphone(self, response):
        self.driver.get(response.request.url)
        tray_count = 0
        while tray_count <= 5:
            try:
                tray_count += 1
                print(f'Parse data about smartphone from {response.request.url} (try {tray_count})', end='  ')
                WebDriverWait(self.driver, 10).until(
                    expected_conditions.presence_of_element_located((By.ID, "section-characteristics"))
                )
                print('OK')
                break
            except Exception:
                self.driver.refresh()
                print(f'FAILED (time limit)')

        sel = Selector(text=self.driver.page_source)
        all_character = sel.xpath('//div[@id="section-characteristics"]//dl')
        characteristics = {}
        for c in all_character:
            key = ''.join(c.xpath('.//dt//text()').extract())
            value = ''.join(c.xpath('.//dd//text()').extract())
            if characteristics.get(key):
                tmp = 1
                while characteristics.get(f'{key}_{tmp}'):
                    tmp += 1
                key = f'{key}_{tmp}'
            characteristics[key] = value

        phone_os = characteristics.get('Операционная система', 'Unknown')

        if phone_os == 'Chrome OS':
            phone_os = 'Android'

        phone__os_value = characteristics.get(f'Версия {phone_os}', 'Unknown')
        clean_v = ' '.join(phone__os_value.split(' ')[:2])
        phone_os_ver = clean_v.split('.')[0]
        title = sel.xpath('//div[@data-widget="webProductHeading"]/h1/text()').get()


        yield {
            'title': title,
            'os': phone_os,
            'os_version': phone_os_ver,
            'url': response.request.url,
            **characteristics,
        }
