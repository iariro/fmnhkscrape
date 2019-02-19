# coding: UTF-8
import datetime
import re
import urllib
import urllib.parse
import urllib.request as urllib2
from bs4 import BeautifulSoup

nowyear = datetime.date.today().year
nowyear1 = "%s" % (nowyear)
nowyear2 = "%s" % (nowyear + 1)

with open(r'..\FUSIONGOL\private\web\fmnhk\fmnhk.html', mode='w') as file:
	file.write("<html>")
	file.write("<head>")
	file.write("<link rel='stylesheet' type='text/css' href='hatena.css'>")
	file.write("</head>")
	file.write("<body>")
	file.write("<div class=hatena-body>")
	file.write("<div class=main>")

	keywords = ["交響曲","受難曲","ドイツ・レクイエム","オネゲル","シェーンベルク","ストラヴィンスキー","ヒナステラ","ライヒ","ラヴェル","ジプシー","ジョエル","スキャッグス","ストラトヴァリウス","マルムスティーン","バルトーク","メシアン","ショスタコーヴィチ"]
	for keyword in keywords:
		# アクセスするURL
		topurl = "http://www2.nhk.or.jp/hensei/program/query.cgi?f=kwd&area=001&qt=%s" % (urllib.parse.quote(keyword))

		print(topurl)
		html = urllib.request.urlopen(topurl)
		soup = BeautifulSoup(html, "html.parser")
		alltd = soup.find_all('td')

		programurls = []
		lastelement = None
		for td in alltd:
			for element in td.children:
				if lastelement == "FM" and element.name == "a":
					programurls.append({"url":element.get("href"), "title":"%s" % element.contents[0].replace("\xa0", "")})
				lastelement = element

		file.write("<h1>%s</h1>\n" % (keyword))
		file.write("<div class=day>")

		# 番組のループ
		for programurl in programurls:
			if '名曲スケッチ' in programurl["title"]:
				continue
			if '名曲の小箱' in programurl["title"]:
				continue

			file.write("<h2>%s</h2>\n" % (programurl["title"]))
			html = urllib.request.urlopen("http://www2.nhk.or.jp/hensei/program/" + programurl["url"])
			soup = BeautifulSoup(html, "html.parser")

			composition = []

			for dd in soup.find_all('dd'):
				for element in dd.children:
					lines = ("%s" % (element)).split("<br/>")
					for line in lines:

						if nowyear1 in line or nowyear2 in line:
							file.write("%s<br>\n" % (line.strip()))
						else:
							if re.match("「.*", line) or "作曲" in line:
								composition.append(line)

							if "作曲" in line:
								if len([line2 for line2 in composition if keyword in line2]) > 0:
									for line2 in composition:
										file.write("%s<br>\n" % (line2))
								composition = []
		file.write("</div>")

	file.write("<br>")
	file.write(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"))
	file.write("<br>")

	file.write("</div>")
	file.write("</div>")
	file.write("</body>")
	file.write("</html>")
