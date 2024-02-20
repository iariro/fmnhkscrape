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
    if len(areas) >= 1:
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
            pp = desc.select("p")
            if len(pp) >= 2:
                for p in pp[1]:
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


def search_digest_2023(keywords):
    time1 = datetime.datetime.now()
    options = ChromeOptions()
    options.add_argument('--headless')
    driver = Chrome(options=options)

    content_title_set = set()
    results = []
    for keyword in keywords:
        url = 'https://www.nhk.jp/timetable/search/?keyword={}&area=130&service=g1,g2,e1,e3,s1,s2,s3,s4,s5,s6,r1,r2,r3'.format(urllib.parse.quote(keyword))
        driver.get(url)

        sleep(5)

        contents = []
        html = driver.page_source.encode('utf-8')
        soup = BeautifulSoup(html, "html.parser")
        table = soup.find('table')
        if table:
            rows = table.find_all('tr')
            if rows:
                i = 0
                for row in rows:
                    cells = row.find_all('td')
                    content = None
                    if cells:
                        j = 0
                        append = True
                        for cell in cells:
                            lines = cell.getText().split()
                            for line in lines:
                                if j in (0, 1):
                                    if '(5分)' in line or '(10分)' in line:
                                        append = False
                                    if content is None:
                                        content = {'title': line, 'text': [], 'type': None}
                                    else:
                                        content['title'] += ' ' + line
                                    if j == 1:
                                        content_title_set.add(content['title'])
                                if j in (2, 3):
                                    if line in ('アニメ', 'ワイルドライフ'):
                                        # append = False
                                        content['type'] = 'exclude'
                                    content['text'].append(line)
                            j += 1
                        if append:
                            contents.append(content)
                    i += 1
        else:
            # TODO エラー判定を実装してエラー出力する
            # contents.append({'title': 'エラー', 'text': ['中断しました']})
            pass
        results.append({'keyword': keyword, 'result': contents})

        # TODO エラー判定を実装してbreakする
        if table is None:
            pass
    time2 = datetime.datetime.now()
    return results, time1, time2, content_title_set


def create_html(all_results, time1, time2, output, content_title_set):
    content_title_use = {text: False for text in content_title_set}
    print(content_title_use)

    with open(output, mode='w') as file:
        file.write("<html>")
        file.write("<head>")
        file.write("<meta http-equiv='Content-Type' content='text/html; charset=UTF-8'>")
        file.write("<link rel='stylesheet' type='text/css' href='hatena.css'>")
        file.write("</head>")
        file.write("<body>")
        file.write("<div class=hatena-body>")
        file.write("<div class=main>")

        file.write(' - '.join(time.strftime("%Y/%m/%d %H:%M:%S") for time in (time1, time2)))
        file.write("<br>")

        for results in all_results:
            file.write("<h1>%s</h1>\n" % (results['keyword']))
            file.write("<div class=day>")
            for program in results['result']:
                duplicate = content_title_use[program['title']]
                file.write("<h2>%s</h2>\n" % (program["title"]))
                if program['text']:
                    exclude = program['type'] == 'exclude'
                    if exclude:
                        file.write("<span class='disable'>\n")
                    for line in program['text']:
                        file.write("%s<br>\n" % (line))
                        if exclude or duplicate:
                            break
                    if exclude:
                        file.write("</span>\n")
                else:
                    file.write("-<br>\n")
                content_title_use[program['title']] = True
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

    results, time1, time2, content_title_set = search_digest_2023(keywords)

    create_html(results, time1, time2, output, content_title_set)

    FTP.encoding = "utf-8"

    # FTP接続.
    ftp = FTP("www2.gol.com", "ip0601170243", passwd="Z#5uqBpt")

    # ファイルのアップロード（テキスト）.
    with open(output, "rb") as f:
        ftp.storlines("STOR /private/web/hobby/fmnhk/fmnhk.html", f)
