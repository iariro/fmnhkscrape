import datetime
import json
import os
import urllib.parse
import urllib.request

def execute_api(date, keywords):
    base_url = "https://api.nhk.or.jp"
    path = "v2/pg/list/200/r3/{}.json".format(date)
    headers = {
        "Accept-Language": "ja_JP",
    }
    query = {
        "key": "AJfq3spYjUQFgcDvQnxACZA44pdgh0Tv"
    }

    # os.pathを使ってURLを結合
    url = os.path.join(base_url, path)

    # クエリストリング
    url_with_query = "{}?{}".format(url, urllib.parse.urlencode(query))

    req = urllib.request.Request(url_with_query, headers=headers)

    # tryでエラーハンドリング
    contents = {keyword: [] for keyword in keywords}
    try:
        with urllib.request.urlopen(req) as res:
            body = res.read().decode("utf-8")
            js = json.loads(body)
            for program in js['list']['r3']:
                for keyword in keywords:
                    if keyword in program['title'] or keyword in program['subtitle']:
                        contents[keyword].append({'title': '{} {}-{}'.format(program['start_time'][0:10], program['start_time'][11:16], program['end_time'][11:16]), 'text': [program['title'], program['subtitle']], 'type': None})
    except urllib.error.HTTPError as e:
        # Status codeでエラーハンドリング
        if e.code >= 400:
            print(e.reason)
        else:
            raise e
    return contents

def find_program_by_api(keywords):
    time1 = datetime.datetime.now()
    contents_all = {keyword: [] for keyword in keywords}
    day = datetime.date.today()
    for i in range(7):
        contents = execute_api(day, keywords)
        for keyword, results in contents.items():
            contents_all[keyword] += results
        day += datetime.timedelta(days=1)
    time2 = datetime.datetime.now()
    return [{'keyword': keyword, 'result': contents_all[keyword]} for keyword in keywords], time1, time2

if __name__ == '__main__':
    keywords = ["交響曲", "受難曲", "ドイツ・レクイエム",
                "オネゲル", "シェーンベルク", "ストラヴィンスキー", "ヒナステラ", "ライヒ", "ラヴェル",
                "バルトーク", "メシアン", "ショスタコーヴィチ"]

    contents_all = find_program_by_api(keywords)
    print(contents_all)
