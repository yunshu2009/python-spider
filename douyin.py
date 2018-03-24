# -*- coding:utf-8 -*-
from bs4 import BeautifulSoup
from contextlib import closing
from tqdm import tqdm
import requests, json, re, os, sys, time


class DouYin(object):
    def __init__(self, path):
        """
        抖音App视频下载
        """
        # SSL认证
        self.path = path
        if not os.path.isdir(path):
            os.mkdir(path)

    def get_video_urls(self, user_id):
        """
        获得视频播放地址
        Parameters:
            nickname：查询的用户名
        Returns:
            video_names: 视频名字列表
            video_urls: 视频链接列表
            aweme_count: 视频数量
        """
        video_names = []
        video_urls = []
        unique_id = ''
        while unique_id != user_id:
            # 不显示https warning错误
            requests.packages.urllib3.disable_warnings()
            search_url = 'https://api.amemv.com/aweme/v1/discover/search/?cursor=0&keyword=%s&count=10&type=1&' \
                         'retry_type=no_retry&iid=17900846586&device_id=34692364855&ac=wifi&channel=xiaomi&' \
                         'aid=1128&app_name=aweme&version_code=162&version_name=1.6.2&device_platform=android&ssmix=a&'\
                         'device_type=MI+5&device_brand=Xiaomi&os_api=24&os_version=7.0&uuid=861945034132187&' \
                         'openudid=dc451556fc0eeadb&manifest_version_code=162&resolution=1080*1920&dpi=480&' \
                         'update_version_code=1622' % user_id
            req = requests.get(url=search_url, verify=False)
            html = json.loads(req.text)
            aweme_count = html['user_list'][0]['user_info']['aweme_count']
            uid = html['user_list'][0]['user_info']['uid']
            nickname = html['user_list'][0]['user_info']['nickname']
            unique_id = html['user_list'][0]['user_info']['unique_id']
        user_url = 'https://www.douyin.com/aweme/v1/aweme/post/?user_id=%s&max_cursor=0&count=%s' % (uid, aweme_count)
        req = requests.get(url=user_url, verify=False)
        html = json.loads(req.text)
        i = 1
        for each in html['aweme_list']:
            share_desc = each['share_info']['share_desc']
            if u'抖音-原创音乐短视频社区' == share_desc:
                video_names.append(str(i) + '.mp4')
                i += 1
            else:
                video_names.append(share_desc + '.mp4')
            video_urls.append(each['share_info']['share_url'])

        return video_names, video_urls, nickname

    def get_download_url(self, video_url):
        """
        获得视频播放地址
        Parameters:
            video_url：视频播放地址
        Returns:
            download_url: 视频下载地址
        """
        req = requests.get(url=video_url, verify=False)
        bf = BeautifulSoup(req.text, 'lxml')
        script = bf.find_all('script')[-1]
        video_url_js = re.findall('var data = \[(.+)\];', str(script))[0]
        video_html = json.loads(video_url_js)
        download_url = video_html['video']['play_addr']['url_list'][0]
        return download_url

    def video_downloader(self, video_url, video_name):
        """
        视频下载
        Parameters:
            None
        Returns:
            None
        """
        size = 0
        # 下载流时，stream=True返回服务器的原始套接字响应，此时你可以访问 r.raw。使用 Response.iter_content 将会处理大量你直接使用
        # Response.raw 不得不处理的
        with closing(requests.get(video_url, stream=True, verify=False)) as response:
            chunk_size = 1024
            content_size = int(response.headers['content-length'])
            if response.status_code == 200:
                sys.stdout.write('  [文件大小]:%0.2f MB\n' % (content_size / chunk_size / 1024))

                with open(video_name, "wb") as file:
                    # Tqdm 是一个快速，可扩展的Python进度条，可以在 Python 长循环中添加一个进度提示信息，用户只需要封装任意的迭代器
                    # tqdm(iterator)。
                    for data in tqdm(response.iter_content(chunk_size=chunk_size)):
                        file.write(data)
                        size += len(data)
                        file.flush()

                    sys.stdout.write('    [下载进度]:%.2f%%' % float(size / content_size * 100))
                    sys.stdout.flush()
        time.sleep(1)

    def run(self):
        """
        运行函数
        Parameters:
            None
        Returns:
            None
        """
        self.hello()
        # user_id = input('请输入ID(例如13978338):')
        user_id = 'sm666888'
        video_names, video_urls, nickname = self.get_video_urls(user_id)

        path = self.path + nickname
        if not os.path.isdir(path):
            os.mkdir(path)
        sys.stdout.write('视频下载中:\n')
        for num in range(len(video_urls)):
            print('  %s\n' % video_urls[num])
            video_url = self.get_download_url(video_urls[num])
            if '\\' in video_names[num]:
                video_name = video_names[num].replace('\\', '')
            elif '/' in video_names[num]:
                video_name = video_names[num].replace('/', '')
            else:
                video_name = video_names[num]
            self.video_downloader(video_url, os.path.join(path, video_name))
            print('')

    def hello(self):
        """
        打印欢迎界面
        Parameters:
            None
        Returns:
            None
        """
        print('*' * 100)
        print('\t\t\t\t抖音App视频下载小助手')
        print('*' * 100)


if __name__ == '__main__':
    path = os.path.dirname(os.path.realpath(__file__)) + '/videos/'
    douyin = DouYin(path)
    douyin.run()
