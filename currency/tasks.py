from datetime import date
from decimal import Decimal

import requests
from celery import shared_task
from requests.exceptions import HTTPError


def db_updater(ccy, buy, sale, source):
    from currency.models import Currency
    cr_last = Currency.objects.filter(currency=ccy, source=source).last()
    if cr_last is None or (cr_last.buy != Decimal(buy) or cr_last.sale != Decimal(sale)):
        Currency.objects.create(currency=ccy, source=source, buy=Decimal(buy), sale=Decimal(sale))


@shared_task
def parse_mono_bank():
    url = "https://api.monobank.ua/bank/currency"
    response = requests.get(url)

    try:
        response = requests.get(url)
        # error if response_status_code will be not 200
        response.raise_for_status()
    except HTTPError as http_err:
        # TODO: log http_error
        pass
    except Exception as err:
        # TODO: log error
        pass

    currency_tags = {840:1,978:2}
    data = response.json()
    for row in data:
        if(row["currencyCodeA"]in currency_tags and row["currencyCodeB"]==980):
            buy = round(Decimal(row["rateBuy"]), 2)
            sale = round(Decimal(row["rateSell"]), 2)
            ccy = str(currency_tags[row["currencyCodeA"]])
            db_updater(ccy, buy, sale, 1)


@shared_task
def parse_vkurse():
    url ="http://vkurse.dp.ua/course.json"
    response = requests.get(url)

    try:
        response = requests.get(url)
        # error if response_status_code will be not 200
        response.raise_for_status()
    except HTTPError as http_err:
        # TODO: log http_error
        pass
    except Exception as err:
        # TODO: log error
        pass

    currency_tags = {'Dollar': 1, 'Euro': 2}
    data = response.json()
    for row in data:
        if row in currency_tags:
            buy = data[row]["buy"]
            sale = data[row]["sale"]
            ccy = str(currency_tags[row])
            db_updater(ccy, buy, sale, 3)


@shared_task
def parse_yahoo():
    from datetime import timedelta

    from yahoofinancials import YahooFinancials
    currencies = ['EURUAH=X', 'USDUAH=X']
    currency_tags = {'USDUAH=X': 1, 'EURUAH=X': 2}

    for cur in currencies:
        cur_yahoo = YahooFinancials(cur)
        yesterday = date.today() - timedelta(days=1)
        buy = round(Decimal(cur_yahoo.get_historical_price_data(str(yesterday), str(yesterday), "daily")
                            [cur]['prices'][0]['close']), 2)
        sale = round(Decimal(cur_yahoo.get_historical_price_data(str(yesterday), str(yesterday), "daily")
                            [cur]['prices'][0]['close']), 2)
        ccy = currency_tags[cur]
        db_updater(ccy, buy, sale, 2)