import requests
import telegram_send as tel
import asyncio
import selenium.common.exceptions
import time
import random
from selenium.webdriver import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
import cv2
import urllib
import numpy as np
import json

def save_image_from_url(url):
    req = urllib.request.urlopen(url)
    arr = np.asarray(bytearray(req.read()), dtype=np.uint8)
    img = cv2.imdecode(arr, -1)
    cv2.imwrite("img.jpg", img)

def send_message(message, image_url=None):
    if(image_url):
        img = save_image_from_url(image_url)
        with open("img.jpg", "rb") as img:
            send = tel.send(images=[img], captions=[message], parse_mode="markdown",
                            disable_web_page_preview=True, conf=f'./telegram.conf')
            asyncio.run(send)
    else:
        send = tel.send(messages=[message], parse_mode="markdown",
                        disable_web_page_preview=True, conf=f'./telegram.conf')
        asyncio.run(send)

def find_all_results(driver: webdriver.Firefox):
    found = []
    # Creiamo un'istanza di Firefox, installiamo un adblocker per saltare le pubblicità
    driver.get("https://www.amazon.it/s?k=4070+ti+super")
    driver.implicitly_wait(2)
    driver.find_element(By.XPATH, '//*[@id="sp-cc-accept"]').click()
    results = driver.find_elements(By.CLASS_NAME, 's-result-item')[1:-4]
    for res in results:
        url = res.find_element(By.TAG_NAME, 'a').get_attribute('href')
        title = res.text.lower().split(' ')[:15]
        
        if("4070" in title and "ti" in title and "super" in title):
            found.append(url.split("ref")[0])
    #driver.quit()
    return found

def check_product(driver: webdriver.Firefox, url):
    driver.get(url)
    driver.implicitly_wait(2)
    print("finding price")
    try:
        price = driver.find_element(By.CLASS_NAME, 'priceToPay').text
        title = driver.find_element(By.ID, 'productTitle').text
    except selenium.common.exceptions.NoSuchElementException:
        price = "not found"
    return(price.replace("\n",","), title)


def main():
    options = webdriver.FirefoxOptions()
    options.add_argument("--headless")
    driver = webdriver.Firefox(options=options)

    # Making list of results
    results = find_all_results(driver)

    # loading previous results
    with open("results.json", "r") as f:
        prev_results = json.loads(f.read())

    # if no prev results, dump all the results in file
    if prev_results == []:
        with open("results.json", "w") as f:
            f.write(json.dumps(results))
    
    # otherwise, add only new results
    else:
        new_results = [res for res in results if res not in prev_results]
        results = prev_results + new_results
        with open("results.json", "w") as f:
            f.write(json.dumps(results))

    print("results: ", results)
    
    quit()
    # checking prices for the first 5 results
    for res in results[:5]:
        print("checking price for: ", res)
        product = check_product(driver, res)
        img_url = driver.find_element(By.ID, 'landingImage').get_attribute('src')
        send_message(f"*{product[1]}*\n\nPrezzo: {product[0]}\n\nLink: {res}", image_url=img_url)
        time.sleep(random.randint(1,5))

if __name__ == "__main__":
    main()