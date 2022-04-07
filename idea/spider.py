import re
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pyquery import PyQuery as pq
import time
import pymongo

KEYWORD ='美食'
MONGO_TABLE = 'meishi'

#把chrome设为selenium驱动的浏览器代理；
browser = webdriver.Chrome()  #登录使用手机扫码
wait = WebDriverWait(browser, 10)



client = pymongo.MongoClient('localhost',27017)
cilen = client['taobao']
db = cilen['meishi']

#打开淘宝网页，进行扫码登陆
def search_page():
    print('正在搜索')
    try:
        browser.get('https://www.taobao.com')
        input = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#q"))
        )
        submit = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#J_TSearchForm > div.search-button > button')))
        input.send_keys(KEYWORD)
        submit.click()
        total = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'#mainsrp-pager > div > div > div > div.total')))
        get_products()
        return total.text
    except TimeoutException:
        return search_page()
#进行翻页处理；
def next_page(page_number):
    print('正在翻页',page_number)
    try:
        input = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#mainsrp-pager > div > div > div > div.form > input"))
        )
        submit = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '#mainsrp-pager > div > div > div > div.form > span.btn.J_Submit')))
        input.clear()
        input.send_keys(page_number)
        submit.click()
        wait.until(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'#mainsrp-pager > div > div > div > ul > li.item.active > span'),str(page_number)))
        get_products()
    except TimeoutException:
        next_page(page_number)
#获取每一页的商品信息；
def get_products():
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'#mainsrp-itemlist .items .item')))
    html = browser.page_source
    doc = pq(html)
    items = doc('#mainsrp-itemlist .items .item').items()
    for item in items:
        product = {
            'price':item.find('.price').text(),
            'deal':item.find('.deal-cnt').text()[:-3],
            'title':item.find('.title').text(),
            'shop':item.find('.shop').text(),
            'location':item.find('.location').text()
        }
        print(product)
        save_to_mongo(product)

#储存到数据库中
def save_to_mongo(result):
    try:
        if db[MONGO_TABLE].insert(result):
            print('存储到MONGO成功',result)
    except Exception:
        print('存储到MONGO失败',result)

#进行递归循环；
def main():
    try:
        total = search_page()
        total = int(re.compile('(\d+)').search(total).group(1))
        for i in range(2,total+1):
            time.sleep(2)
            next_page(i)
    except Exception:
        print('出错了')
    finally:
        browser.close()

#启动爬虫
if __name__ == '__main__':
    main()