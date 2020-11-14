#!/usr/bin/python3

import datetime
import re
import urllib
import urllib.parse
import urllib.request
from bs4 import BeautifulSoup
from ftplib import FTP

def find_program(keywords):
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

        for results in all_results:
            file.write("<h1>%s</h1>\n" % (results['keyword']))
            file.write("<div class=day>")
            for program in results['result']:
                file.write("<h2>%s</h2>\n" % (program["title"]))
                for line in program['text']:
                    file.write("%s<br>\n" % (line))
            file.write("</div>")

        file.write("<br>")
        file.write(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"))
        file.write("<br>")

        file.write("</div>")
        file.write("</div>")
        file.write("</body>")
        file.write("</html>")


if __name__ == '__main__':
    keywords = ["交響曲", "受難曲", "ドイツ・レクイエム",
                "オネゲル", "シェーンベルク", "ストラヴィンスキー", "ヒナステラ", "ライヒ", "ラヴェル",
                "ジプシー", "ジョエル", "スキャッグス", "ストラトヴァリウス", "マルムスティーン",
                "バルトーク", "メシアン", "ショスタコーヴィチ"]

    output = '/home/pi/ドキュメント/python/fmnhkscrape/fmnhk.html'
    results = find_program(keywords)
    create_html(results, output)

    FTP.encoding = "utf-8"

    # FTP接続.
    ftp = FTP("www2.gol.com", "ip0601170243", passwd="Z#5uqBpt")

    # ファイルのアップロード（テキスト）.
    with open(output, "rb") as f:  # 注意：バイナリーモード(rb)で開く必要がある
        ftp.storlines("STOR /private/web/hobby/fmnhk/fmnhk.html", f)
