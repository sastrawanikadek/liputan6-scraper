import os
from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from pymongo import MongoClient
from datetime import datetime, timedelta

chrome_options = ChromeOptions()
chrome_options.binary_location = os.environ.get('GOOGLE_CHROME_BIN')
chrome_options.add_argument('--headless')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--no-sandbox')

driver = Chrome(executable_path=os.environ.get('CHROMEDRIVER_PATH'), chrome_options=chrome_options)
wait = WebDriverWait(driver, 15)
client = MongoClient(os.environ.get('MONGODB_URI'))
db = client['hoax-detection']
collection = db['train-datasets']
today = datetime.today()


def get_article(url):
    driver.execute_script(f'window.open("{url}")')
    driver.switch_to.window(driver.window_handles[1])

    article = wait.until(lambda drv: drv.find_element_by_css_selector('article.hentry.main'))
    article_title_element = article.find_element_by_css_selector('h1.read-page--header--title.entry-title')
    article_date_element = article.find_element_by_css_selector('time.read-page--header--author__datetime.updated')
    article_author_element = article.find_element_by_css_selector('span.read-page--header--author__name.fn')
    article_content_element = article.find_elements_by_css_selector('.article-content-body__item-page p')

    article_title = article_title_element.text
    article_date = article_date_element.get_attribute('datetime')
    article_author = article_author_element.text
    article_content = ""

    for content_element in article_content_element:
        if content_element.get_attribute('class') is not None:
            continue

        article_content += f'{content_element.text}\n'

    if not collection.find_one({'url': url}):
        collection.insert_one({
            'url': url,
            'title': article_title,
            'date': article_date,
            'author': article_author,
            'content': article_content,
            'class': 'Valid'
        })

    driver.close()
    driver.switch_to.window(driver.window_handles[0])


def get_all_articles(date, page=1):
    url = f'https://www.liputan6.com/news/indeks/{date.year}/{date.month:02d}/{date.day:02d}?page={page}'
    driver.get(url)

    try:
        articles = wait.until(lambda drv: drv.find_elements_by_css_selector('article.articles--rows--item'))

        for article in articles:
            article_url_element = article.find_element_by_css_selector('a.articles--rows--item__title-link')
            article_url = article_url_element.get_attribute('href')
            get_article(article_url)

        get_all_articles(date, page + 1)
    except TimeoutException:
        get_all_articles(date - timedelta(days=1))


get_all_articles(datetime.today())
