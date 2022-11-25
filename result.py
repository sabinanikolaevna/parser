from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from ozon_phone.spiders.phones_spider import PhonesSpiders
import os
import pandas as pd

DATA_FILE_NAME = 'result.csv'

MAX_SMARTPHONE = 100

if __name__ == "__main__":
    settings = get_project_settings()
    SETTING = {
        **settings,
        'FEEDS': {
            DATA_FILE_NAME: {
                'format': 'csv',
            }
        },
        'LOG_LEVEL': 'ERROR',
    }


    PhonesSpiders.custom_settings = {
        'LOG_LEVEL': 'ERROR',
    }

    PhonesSpiders.MAX_SMARTPHONE = MAX_SMARTPHONE


    if os.path.exists(DATA_FILE_NAME):
        os.remove(DATA_FILE_NAME)


    process = CrawlerProcess(settings=SETTING)
    process.crawl(PhonesSpiders)
    process.start()


    try:
        phone_stats = pd.read_csv(DATA_FILE_NAME)
        stats_os_version = phone_stats['os_version'].value_counts()
        print('OS VERSION:')
        for i in stats_os_version.index:
            print(f'{i} - {stats_os_version[i]}')
        print(f'Total: {sum(stats_os_version)}')
    except Exception as e:
        print(f'WARNING: {e}')
