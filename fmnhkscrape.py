#!/usr/bin/python3

import datetime
from time import sleep
import re
import urllib
import urllib.parse
import urllib.request
import bs4
from bs4 import BeautifulSoup
from ftplib import FTP
from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver.common.keys import Keys

def get_program_information(url):
    options = ChromeOptions()
    options.add_argument('--headless')
    driver = Chrome(options=options)

    driver.get(url)

    sleep(5)

    contents = []
    content = {}
    contents.append(content)
    html = driver.page_source.encode('utf-8')
    soup = BeautifulSoup(html, "html.parser")
    areas = soup.select("section[class='program-area']")
    for onair in areas[0].select("div[class='program-title-area']"):
        program_time = onair.select_one("div[class='program-time large']")
        if program_time is None:
            continue
        program_time = program_time.select("time")
        content['start_time'] = program_time[0]['datetime'][0:-3]
        content['end_time'] = program_time[1]['datetime'][-8:-3]
    content['text'] = []
    desc = areas[0].select_one("div[class='program-description col-12']")
    if desc is not None:
        for p in desc.select("p")[1]:
            if isinstance(p, bs4.element.NavigableString):
                line = str(p)
                if not line.startswith('「') and not line.endswith('作曲'):
                    line = '　' + line
                content['text'].append(line)

    content = {}
    contents.append(content)
    if len(areas) >= 2:
        onair = areas[1].select("section[class='program-onair clear']")
        onair += areas[1].select("section[class='program-onair']")
        for onair in onair:
            program_time = onair.select_one("div[class='program-time medium']")
            program_time = program_time.select("time")
            content['start_time'] = program_time[0]['datetime'][0:-3]
            content['end_time'] = program_time[1]['datetime'][-8:-3]
            content['text'] = []
            for music in onair.select("div[class='program-onair-music']"):
                for li in music.find("li"):
                    if isinstance(li, bs4.element.NavigableString):
                        line = str(li)
                        if not line.startswith('「') and not line.endswith('作曲'):
                            line = '　' + line
                        content['text'].append(line)
    driver.close()
    driver.quit()
    return contents

def find_program_2020(keywords):
    user_agent = "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:47.0) Gecko/20100101 Firefox/47.0"
    headers = {"User-Agent": user_agent}

    nowyear = datetime.date.today().year
    nowyear1 = "%s" % (nowyear)
    nowyear2 = "%s" % (nowyear + 1)

    all_results = []
    for keyword in keywords:
        try:
            # アクセスするURL
            topurl = "https://www2.nhk.or.jp/hensei/program/query.cgi?f=kwd&area=001&qt=%s"
            topurl = topurl % (urllib.parse.quote(keyword))

            request = urllib.request.Request(topurl, headers=headers)
            html = urllib.request.urlopen(request)
            soup = BeautifulSoup(html, "html.parser")
            alltd = soup.find_all('td')

            programurls = []
            lastelement = None
            for td in alltd:
                for element in td.children:
                    if lastelement == "FM" and element.name == "a":
                        programurls.append({"url": element.get("href"),
                                            "title": element.contents[0].replace("\xa0", "")})
                    lastelement = element

            results = []
            all_results.append({'keyword': keyword, 'result': results})

            # 番組のループ
            for programurl in programurls:
                if '名曲スケッチ' in programurl["title"]:
                    continue
                if '名曲の小箱' in programurl["title"]:
                    continue

                result = {'title': programurl["title"], 'text': []}
                results.append(result)
                programurl2 = "http://www2.nhk.or.jp/hensei/program/" + programurl["url"]
                request2 = urllib.request.Request(programurl2, headers=headers)
                html = urllib.request.urlopen(request2)
                soup = BeautifulSoup(html, "html.parser")

                composition = []

                for dd in soup.find_all('dd'):
                    for element in dd.children:
                        lines = ("%s" % (element)).split("<br/>")
                        for line in lines:
                            if nowyear1 in line or nowyear2 in line:
                                result['text'].append(line.strip())
                            else:
                                if re.match("「.*", line) or "作曲" in line:
                                    composition.append(line)

                                if "作曲" in line:
                                    if len([c for c in composition if keyword in c]) > 0:
                                        for c in composition:
                                            result['text'].append(c)
                                    composition = []
        except Exception:
            pass

    return all_results

def create_html(all_results, output):
    with open(output, mode='w') as file:
        file.write("<html>")
        file.write("<head>")
        file.write("<meta http-equiv='Content-Type' content='text/html; charset=UTF-8'>")
        file.write("<link rel='stylesheet' type='text/css' href='hatena.css'>")
        file.write("</head>")
        file.write("<body>")
        file.write("<div class=hatena-body>")
        file.write("<div class=main>")

        file.write(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"))
        file.write("<br>")

        for results in all_results:
            file.write("<h1>%s</h1>\n" % (results['keyword']))
            file.write("<div class=day>")
            for program in results['result']:
                file.write("<h2>%s</h2>\n" % (program["title"]))
                for line in program['text']:
                    file.write("%s<br>\n" % (line))
            file.write("</div>")

        file.write("<br>")

        file.write("</div>")
        file.write("</div>")
        file.write("</body>")
        file.write("</html>")


if __name__ == '__main__':
    keywords = ["交響曲", "受難曲", "ドイツ・レクイエム",
                "オネゲル", "シェーンベルク", "ストラヴィンスキー", "ヒナステラ", "ライヒ", "ラヴェル",
                "バルトーク", "メシアン", "ショスタコーヴィチ"]

    output = '/home/pi/doc/private/python/fmnhkscrape/fmnhk.html'

    urls = [{ 'title': 'ブラボー！オーケストラ', 'url': 'https://www4.nhk.or.jp/bravo/'},
            { 'title': 'クラシックカフェ', 'url': 'https://www4.nhk.or.jp/c-cafe/'},
            { 'title': 'ベストオブクラシック', 'url': 'https://www4.nhk.or.jp/bescla/' }]
    contents = {}
    for url in urls:
        contents[url['title']] = get_program_information(url['url'])
    results = []
    for keyword in keywords:
        result = {'keyword': keyword, 'result': []}
        results.append(result)
        for title, content in contents.items():
            for content2 in content:
                if 'text' in content2:
                    if len([line for line in content2['text'] if keyword in line]) > 0:
                        title2 = '%s %s-%s' % (title,
                                               content2['start_time'].replace('-', '/'),
                                               content2['end_time'].replace('-', '/'))
                        result['result'].append({'title': title2, 'text': content2['text']})

    create_html(results, output)

    FTP.encoding = "utf-8"

    # FTP接続.
    ftp = FTP("www2.gol.com", "ip0601170243", passwd="Z#5uqBpt")

    # ファイルのアップロード（テキスト）.
    with open(output, "rb") as f:
        ftp.storlines("STOR /private/web/hobby/fmnhk/fmnhk.html", f)
