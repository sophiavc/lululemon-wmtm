import time
import datetime
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException


MAX_THREADS = 20
CATEGORIES = {}  # dictionary of category names : list of product names
PRODUCTS = {}  # dictionary of product names : list of Product objects (specific colors)
PRODUCT_URLS = {}  # dictionary of product names : URL


class Product:
    def __init__(self, name, color, price, sizes, url):
        self.name = name
        self.color = color
        self.price = price
        self.sizes = sizes
        self.url = url


def get_html(driver, url):
    # return requests.get(url).text

    driver.get(url)  # open WMTM page

    # do while loop to load all products
    while True:
        driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')  # scroll to bottom of page
        time.sleep(3)  # allow time to load

        try:  # try to locate button to view more products
            button = driver.find_element_by_xpath("//span[text()='View more products']")
            actions = ActionChains(driver)
            actions.move_to_element(button).perform()  # move button into view
            button.click()  # click to view more products

        except NoSuchElementException:  # all products loaded
            break

    return driver.page_source  # return HTML text


def get_links(html):
    links = []  # list of product urls

    soup = BeautifulSoup(html, 'html.parser')
    items = soup.find('div', class_='product-list').find('div', class_='row')\
        .find_all('div', class_='col-xs-6 col-sm-4 product-list__item')  # all items in tags

    for i in items:  # get links to items using a tags
        url = i.find('a').get('href')
        links.append('https://shop.lululemon.com' + url)

    return links


def get_product_details(driver, links):
    try:
        for l in links:
            try:
                driver.get(l)  # open product page

                name = driver.find_element_by_xpath("//div[@itemprop='name']").text  # get name
                name = name.replace('\n', ' ')

                category = driver.find_element_by_xpath("//ul[@class='breadcrumbs-1Pb7p breadcrumbs']") \
                    .find_elements_by_tag_name('li')[-1].text  # get category

                if name not in PRODUCTS:  # if this is the first time we encounter this product name
                    PRODUCTS[name] = []  # add to products dict and init empty list as value
                    PRODUCT_URLS[name] = l.replace('.com//', '.com/')

                    if category not in CATEGORIES:  # if this is the first time we encounter this category
                        CATEGORIES[category] = []  # add to categories dict and init empty list as value

                    CATEGORIES[category].append(name)  # regardless, append product name to category list

                for c in driver.find_element_by_class_name('purchase-attributes__color-selector') \
                        .find_elements_by_css_selector("div[role='radio']"):  # find all colors
                    color = c.get_attribute('aria-label')
                    if color.endswith('(out of stock)'):  # remove out of stock from color name if needed
                        color = color[:-14].strip()

                    c.click()  # click on the color swatch to get sizes and price

                    sizes = []  # list of avail sizes
                    for s in driver.find_element_by_class_name('purchase-attributes__select-size') \
                            .find_elements_by_css_selector("div[role='radio']"):  # find all sizes
                        if '(not available)' not in s.text:
                            if s.text.isdigit():  # append to list as int or string
                                sizes.append(int(s.text))
                            else:
                                sizes.append(s.text)

                        if int(s.get_attribute('tabindex')) == 0:
                            s.click()  # click on first size avail to get the price

                            price = driver.find_element_by_xpath("//span[@class='price-1SDQy price']").text
                            if len(price) > 0:
                                idx1 = price.find('$')
                                idx2 = price.find('.')
                                price = price[idx1:idx2+3]
                            else:
                                price = 'N/A'

                    if len(sizes) > 0:
                        color = Product(name, color, price, sizes, driver.current_url)
                        PRODUCTS[name].append(color)
            except:
                pass
    except:
        pass


def main():
    start = time.time()

    driver = webdriver.Chrome('/Users/sophiachen/chromedriver')
    url = 'https://shop.lululemon.com/c/sale/_/N-1z0xcuuZ8t6'

    get_product_details(driver, get_links(get_html(driver, url)))

    now = datetime.datetime.now()
    file_name = 'wmtm_' + now.strftime("%Y-%m-%d %H:%M:%S") + '.txt'
    file = open(file_name, 'w')

    for category in CATEGORIES:  # iterate through dict
        file.write('**' + category.upper() + '**\n')  # key

        product_names = CATEGORIES[category]  # value
        product_names.sort()  # alphabetically sort

        for product in product_names:
            colors = PRODUCTS[product]  # get list of Product objs (for each color)

            if len(colors) > 0:
                file.write('[' + product + ']' + '(' + PRODUCT_URLS[product] + ')\n')

                colors = PRODUCTS[product]
                for c in colors:
                    file.write(c.color + ' | ' + c.price + ' | ' + ', '.join(str(i) for i in c.sizes) + '\n')

                file.write('\n')

        file.write('\n')

    file.close()
    end = time.time()
    print('Time elapsed:', str(end - start), 'seconds')


main()
