import os
from datetime import datetime
import logging
import shutil

from flask import Flask, render_template, request
import mechanicalsoup
from bs4 import BeautifulSoup
import requests


class CycleApp:
    def __init__(self, app_name):
        self.items_list = None
        self.app = Flask(app_name)
        self.app.route('/')(self.index)
        self.app.route('/index')(self.index)
        self.app.run(host='0.0.0.0', debug=False, port=8080)
        self.logger = logging.Logger(app_name)

    @staticmethod
    def log_visitor():
        visitor_ip = request.remote_addr
        visitor_requested_path = request.full_path
        now = datetime.now()
        dt = now.strftime("%d/%m/%Y %H:%M:%S")

        pth = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(pth, "log.txt"), "a") as f:
            f.write(f"{dt}: {visitor_ip} {visitor_requested_path}")
            f.close()

    def index(self):
        self.log_visitor()
        if self.items_list is None:
            self.populate_items()

        return render_template('index.html', items_list=self.items_list)

    def download_images(self):
        url = "https://thecyclefrontier.fandom.com/wiki/Loot"
        page = requests.get(url)

        soup = BeautifulSoup(page.text)
        rows = soup.find("div", {"id": "content"}).find("tbody").find_all("tr")

        for row in rows:
            cells = row.find_all("td")

            if len(cells) > 0:
                if cells[1].string is None:
                    if cells[1].find("span") is not None:
                        name = cells[1].find("span").string.strip()
                    elif cells[1].find("a") is not None:
                        name = cells[1].find("a").string.strip()
                    else:
                        raise Exception(f"an issue with cells occurred, {cells[1]}")
                else:
                    name = cells[1].string.strip()

                if cells[0].find("img") is not None:
                    self.logger.debug(cells[0])
                    image_src = cells[0].find("a")['href']
                    img = requests.get(image_src, stream=True)
                    file_path = os.path.join(os.getcwd(), "static", "img", f"{name}.png")
                    with open(file_path, 'wb') as f:
                        img.raw.decode_content = True
                        shutil.copyfileobj(img.raw, f)

    def populate_items(self):
        self.items_list = []
        url = "https://thecyclefrontier.fandom.com/wiki/Loot"
        browser = mechanicalsoup.Browser()
        page = browser.get(url)

        soup = page.soup
        rows = soup.find("div", {"id": "content"}).find("tbody").find_all("tr")

        item_no = 0
        for row in rows:
            cells = row.find_all("td")
            name = ""
            link = ""
            image_src = ""
            weight = ""
            sell_price = ""
            price_per_weight = ""

            if len(cells) > 0:
                if cells[1].string is None:
                    if cells[1].find("span") is not None:
                        name = cells[1].find("span").string.strip()
                    elif cells[1].find("a") is not None:
                        name = cells[1].find("a").string.strip()
                        link = cells[1].find("a", href=True)['href']
                        link = link.replace("/wiki", "https://thecyclefrontier.fandom.com/wiki")
                else:
                    name = cells[1].string.strip()

                if cells[0].find("img") is not None:
                    image_src = f"img/{name}.png"

                if cells[2].string is not None:
                    weight = cells[2].string.strip()

                if cells[3].string is not None:
                    sell_price = cells[3].string.strip()

                if cells[4].string is not None:
                    price_per_weight = cells[4].string.strip()

                item = {
                    "id": str(len(self.items_list)),
                    "name": name,
                    "link": link,
                    "image_src": image_src,
                    "weight": weight,
                    "price_per_weight": price_per_weight,
                    "sell_price": sell_price
                }
                self.items_list.append(item)


if __name__ == '__main__':
    CycleApp(__name__)
