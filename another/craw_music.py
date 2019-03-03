# --*-- coding:utf-8 --*--
import requests
import re
import json


class KuGou(object):

    def get_kg_music_list(self, music_name):
        url = "http://songsearch.kugou.com/song_search_v2?callback=jQuery112407470964083509348_1534929985284&keyword={}&" \
              "page=1&pagesize=30&userid=-1&clientver=&platform=WebFilter&tag=em&filter=2&iscorrection=1&privilege_filte" \
              "r=0&_=1534929985286".format(music_name)
        try:
            res = requests.get(url).text
            js = json.loads(res[res.index('(') + 1:-2])
            data = js['data']['lists']
        except TimeoutError:
            return {"status": 0, "error": "TimeOut"}
        except:
            return {"status": 0, "error": "Not Found"}
        song_list = []
        for i in range(20):
            try:
                song_index = str(i)
                song = str(data[i]['FileName']).replace('<em>', '').replace('</em>', '')
                singer = re.findall('(^.*?)-.*', song)[0].strip()
                song_url = "https://www.kugou.com/song/#hash={}&album_id={}".format(data[i]['FileHash'], data[i]['AlbumID'])
                song_name = re.findall('.*-(.*)', song)[0].strip()
                # song_url = data
                song_list.append({"song_index": song_index,
                                  "song_name": song_name,
                                  "singer": singer,
                                  "song_platform": "kg",
                                  "song_url": song_url})  # kg是音乐平台
            except:
                return {"status": 0, "error": "Not Found"}
        return song_list

    def download(self, music_name, song_index):
        """
        根据索引获取相应的歌曲下载链接
        :param music_name: 歌名
        :param song_index: 歌曲索引
        :return: song_url
        """
        url = "http://songsearch.kugou.com/song_search_v2?callback=jQuery112407470964083509348_1534929985284&keyword={}&" \
              "page=1&pagesize=30&userid=-1&clientver=&platform=WebFilter&tag=em&filter=2&iscorrection=1&privilege_filte" \
              "r=0&_=1534929985286".format(music_name)
        try:
            song_index = int(song_index)
            res = requests.get(url).text
            fhash = re.findall('"FileHash":"(.*?)"', res)[song_index]
            hash_url = "http://www.kugou.com/yy/index.php?r=play/getdata&hash=" + fhash
            hash_content = requests.get(hash_url)
            play_url = ''.join(re.findall('"play_url":"(.*?)"', hash_content.text))
            song_url = play_url.replace("\\", "")
            return song_url
        except Exception as e:
            return None


class QQMusic(object):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/7'
                             '1.0.3578.80 Safari/537.36'}

    def comment(self, music_name):
        url1 = 'https://c.y.qq.com/soso/fcgi-bin/client_search_cp?&t=0&aggr=1' \
               '&cr=1&catZhida=1&lossless=0&flag_qc=0&p=1&n=20&w=' + music_name
        try:
            response = requests.get(url1, headers=QQMusic.headers)
            if response.status_code != 200:
                return "error"
            js_of_rest1 = json.loads(response.text.strip('callback()[]'))
            js_of_rest1 = js_of_rest1['data']['song']['list']
        except TimeoutError:
            return {"status": 0, "error": "TimeOut"}
        except:
            return {"status": 0, "error": "Not Found"}
        return js_of_rest1

    def get_qq_music_list(self, music_name):
        js_of_rest1 = self.comment(music_name)
        singers = []
        song_list = []
        count = 0
        for rest in js_of_rest1:
            song_url = "https://y.qq.com/n/yqq/song/{}.html".format(rest["media_mid"])
            try:
                singers.append(rest['singer'][0]['name'])
                song_list.append({"song_index": count,
                                  "song_name": rest["songname"],
                                  "singer": rest["singer"][0]["name"],
                                  "song_url": song_url,
                                  "song_platform": "qq"})
                count += 1
            except:
                return {"status": 0, "error": "404!"}
        return song_list

    def download(self, music_name, song_index):
        song_index = int(song_index)
        js_of_rest1 = self.comment(music_name)
        url2 = 'https://c.y.qq.com/base/fcgi-bin/fcg_music_express_mobile3.fcg?&jsonpCallback=MusicJsonCallback&cid=' \
               '205361747&songmid=' + js_of_rest1[song_index]['songmid'] + '&filename=C400' + js_of_rest1[song_index]['media_mid'] + '.m4a&guid=6612300644'
        response = requests.get(url2, headers=QQMusic.headers)
        if response.status_code != 200:
            return {"status": 0, "error": "404!"}
        js_of_rest2 = json.loads(response.text)
        vkey = js_of_rest2['data']['items'][0]['vkey']
        song_url = 'http://dl.stream.qqmusic.qq.com/C400' + js_of_rest1[song_index][
            'media_mid'] + '.m4a?vkey=' + vkey + '&guid=6612300644&uin=0&fromtag=66'
        return song_url


# if __name__ == '__main__':
#     music_name = input(">>")
#     song_l = KuGou()
#     songs_list = song_l.get_kg_music_list(music_name)
#     print(songs_list)
#     index = input("下载序号>>")
#     song_u = song_l.download(music_name, index)
#     print(song_u)


if __name__ == '__main__':
    music_name = input(">>")
    song_l = QQMusic()
    songs_list = song_l.get_qq_music_list(music_name)
    print(songs_list)
    index = input("下载序号>>")
    song_u = song_l.download(music_name, index)
    print(song_u)


