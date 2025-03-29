from bs4 import BeautifulSoup
import logging
import time
import random
import requests
import os
import traceback

from util.common_util import CommonUtil
from util.llm_util import LLMUtil
from util.oss_util import OSSUtil

llm = LLMUtil()
oss = OSSUtil()

# 设置日志记录
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(filename)s - %(funcName)s - %(lineno)d - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

global_agent_headers = [
    "Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:30.0) Gecko/20100101 Firefox/30.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.75.14 (KHTML, like Gecko) Version/7.0.3 Safari/537.75.14",
    "Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.2; Win64; x64; Trident/6.0)",
    'Mozilla/5.0 (Windows; U; Windows NT 5.1; it; rv:1.8.1.11) Gecko/20071127 Firefox/2.0.0.11',
    'Opera/9.25 (Windows NT 5.1; U; en)',
    'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; .NET CLR 1.1.4322; .NET CLR 2.0.50727)',
    'Mozilla/5.0 (compatible; Konqueror/3.5; Linux) KHTML/3.5.5 (like Gecko) (Kubuntu)',
    'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.8.0.12) Gecko/20070731 Ubuntu/dapper-security Firefox/1.5.0.12',
    'Lynx/2.8.5rel.1 libwww-FM/2.14 SSL-MM/1.4.1 GNUTLS/1.2.9',
    "Mozilla/5.0 (X11; Linux i686) AppleWebKit/535.7 (KHTML, like Gecko) Ubuntu/11.04 Chromium/16.0.912.77 Chrome/16.0.912.77 Safari/535.7",
    "Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:10.0) Gecko/20100101 Firefox/10.0 "
]

class WebsitCrawler:
    def __init__(self):
        pass  # 不再需要初始化浏览器

    # 爬取指定URL网页内容
    async def scrape_website(self, url, tags, languages):
        # 开始爬虫处理
        try:
            # 记录程序开始时间
            start_time = int(time.time())
            logger.info("正在处理：" + url)
            
            # 确保 URL 格式正确
            if not url.startswith('http://') and not url.startswith('https://'):
                url = 'https://' + url

            # 使用 requests 替代 pyppeteer
            headers = {'User-Agent': random.choice(global_agent_headers)}
            try:
                response = requests.get(url, headers=headers, timeout=30, verify=False)
                response.raise_for_status()  # 确保请求成功
            except Exception as e:
                logger.error(f"获取页面内容失败: {url}, 错误: {str(e)}")
                # 尝试再次请求，忽略 SSL 验证
                try:
                    response = requests.get(url, headers=headers, timeout=30, verify=False)
                except Exception as e:
                    logger.error(f"第二次尝试获取页面内容失败: {url}, 错误: {str(e)}")
                    return None

            # 使用 BeautifulSoup 解析 HTML
            origin_content = response.text
            soup = BeautifulSoup(origin_content, 'html.parser')

            # 通过标签名提取内容
            title = soup.title.string.strip() if soup.title and soup.title.string else ''

            # 根据url提取域名生成name
            name = CommonUtil.get_name_by_url(url)

            # 获取网页描述
            description = ''
            meta_description = soup.find('meta', attrs={'name': 'description'})
            if meta_description and 'content' in meta_description.attrs:
                description = meta_description['content'].strip()

            if not description:
                meta_description = soup.find('meta', attrs={'property': 'og:description'})
                if meta_description and 'content' in meta_description.attrs:
                    description = meta_description['content'].strip()
            
            # 如果仍然没有描述，尝试使用首段文本
            if not description:
                first_p = soup.find('p')
                if first_p and first_p.text:
                    description = first_p.text.strip()[:200]  # 限制长度
            
            logger.info(f"url:{url}, title:{title}, description:{description}")

            # 不再生成网站截图，而是尝试获取网站的 favicon 或 logo
            image_key = oss.get_default_file_key(url)
            screenshot_key = None
            thumnbail_key = None
            
            # 尝试获取网站的 favicon 或 logo
            favicon = soup.find('link', rel='icon') or soup.find('link', rel='shortcut icon')
            logo = soup.find('meta', property='og:image')
            
            favicon_url = None
            if favicon and 'href' in favicon.attrs:
                favicon_url = favicon['href']
            elif logo and 'content' in logo.attrs:
                favicon_url = logo['content']
                
            if favicon_url:
                # 处理相对路径
                if favicon_url.startswith('/'):
                    # 构建绝对 URL
                    from urllib.parse import urlparse
                    parsed_url = urlparse(url)
                    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
                    favicon_url = base_url + favicon_url
                
                try:
                    # 下载图标
                    icon_response = requests.get(favicon_url, headers=headers, timeout=10, verify=False)
                    if icon_response.status_code == 200:
                        icon_path = f"./{name}_favicon.ico"
                        with open(icon_path, 'wb') as f:
                            f.write(icon_response.content)
                        # 上传图标
                        screenshot_key = oss.upload_file_to_r2(icon_path, image_key)
                        thumnbail_key = screenshot_key  # 使用同一个图标作为缩略图
                except Exception as e:
                    logger.error(f"下载网站图标失败: {favicon_url}, 错误: {str(e)}")

            # 抓取整个网页内容
            content = soup.get_text()

            # 使用llm工具处理content
            detail = None
            try:
                detail = llm.process_detail(content)
            except Exception as e:
                logger.error(f"处理内容失败: {str(e)}")
                # 如果 LLM 处理失败，使用简单文本作为详情
                detail = f"# {title}\n\n{description}\n\n"
                
                # 提取一些有意义的段落
                paragraphs = soup.find_all('p')
                for i, p in enumerate(paragraphs[:10]):  # 只提取前10个段落
                    text = p.get_text().strip()
                    if len(text) > 50:  # 只添加有意义的段落
                        detail += f"{text}\n\n"
                    if len(detail) > 1000:  # 限制长度
                        break

            # 如果tags为非空数组，则使用llm工具处理tags
            processed_tags = None
            try:
                if tags and detail:
                    processed_tags = llm.process_tags('tag_list is:' + ','.join(tags) + '. content is: ' + detail)
            except Exception as e:
                logger.error(f"处理标签失败: {str(e)}")

            # 循环languages数组， 使用llm工具生成各种语言
            processed_languages = []
            try:
                if languages:
                    for language in languages:
                        logger.info(f"正在处理{url}站点，生成{language}语言")
                        processed_title = llm.process_language(language, title)
                        processed_description = llm.process_language(language, description)
                        processed_detail = llm.process_language(language, detail)
                        processed_languages.append({'language': language, 'title': processed_title,
                                                  'description': processed_description, 'detail': processed_detail})
            except Exception as e:
                logger.error(f"处理语言翻译失败: {str(e)}")

            logger.info(f"{url}站点处理成功")
            return {
                'name': name,
                'url': url,
                'title': title,
                'description': description,
                'detail': detail,
                'screenshot_data': screenshot_key,
                'screenshot_thumbnail_data': thumnbail_key,
                'tags': processed_tags,
                'languages': processed_languages,
            }
        except Exception as e:
            logger.error(f"处理{url}站点异常，错误信息: {str(e)}")
            logger.error(traceback.format_exc())
            return None
        finally:
            # 计算程序执行时间
            execution_time = int(time.time()) - start_time
            # 输出程序执行时间
            logger.info(f"处理{url}用时：{execution_time}秒")
