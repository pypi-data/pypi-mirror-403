"""
HasData 第三方服务
提供 Google SERP 搜索和 Web Scrape 网页抓取能力

所有配置已硬编码在代码中
"""
import asyncio
import logging
from typing import Optional, List, Dict
from dataclasses import dataclass, field
import httpx


# ============ 硬编码配置 ============
HASDATA_API_KEY = "490dcadd-4ed0-4afc-a34c-c94d100f0702"


# Google 搜索时间过滤参数常量
TBS_PAST_DAY = "qdr:d"      # 过去一天
TBS_PAST_WEEK = "qdr:w"     # 过去一周
TBS_PAST_MONTH = "qdr:m"    # 过去一个月
TBS_PAST_6_MONTHS = "qdr:m6"  # 过去6个月
TBS_PAST_YEAR = "qdr:y"     # 过去一年

# 默认语言
DEFAULT_LANGUAGE = "en"


@dataclass
class SerpResult:
    """搜索结果项"""
    url: str
    title: str
    description: str
    raw_content: str = ""  # 用于 GPT Researcher


@dataclass
class ScrapeResult:
    """爬取结果"""
    url: str
    content: str
    title: str = ""
    image_urls: List[str] = field(default_factory=list)


class HasDataService:
    """
    HasData 第三方服务

    提供:
    - Google Light SERP 搜索
    - Web Scrape 网页抓取
    """

    GOOGLE_LIGHT_SERP_URL = "https://api.hasdata.com/scrape/google-light/serp"
    WEB_SCRAPE_URL = "https://api.hasdata.com/scrape/web"
    TIMEOUT_SECONDS = 300

    # 信号量控制并发 - 使用字典存储每个事件循环的信号量
    _semaphores: Dict[asyncio.AbstractEventLoop, asyncio.Semaphore] = {}
    MAX_CONCURRENT = 13

    def __init__(self):
        self.api_key = HASDATA_API_KEY
        self.logger = logging.getLogger(__name__)

        if not self.api_key:
            self.logger.warning("HASDATA_API_KEY 未配置，HasData 服务将不可用")

    @classmethod
    def _get_semaphore(cls) -> asyncio.Semaphore:
        """获取当前事件循环的信号量（懒加载）"""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            # 如果没有运行中的事件循环，创建一个新的信号量
            return asyncio.Semaphore(cls.MAX_CONCURRENT)

        # 为每个事件循环创建独立的信号量
        if loop not in cls._semaphores:
            cls._semaphores[loop] = asyncio.Semaphore(cls.MAX_CONCURRENT)

        return cls._semaphores[loop]

    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        return {
            "x-api-key": self.api_key,
            "Content-Type": "application/json"
        }

    async def search_google(
        self,
        query: str,
        max_results: int = 10,
        location: Optional[str] = None,
        tbs: Optional[str] = None,
        language: str = DEFAULT_LANGUAGE
    ) -> List[SerpResult]:
        """
        Google Light SERP 搜索

        Args:
            query: 搜索关键词
            max_results: 最大结果数
            location: 地理位置
            tbs: 时间过滤 (TBS_PAST_DAY, TBS_PAST_WEEK 等)
            language: 语言代码

        Returns:
            搜索结果列表
        """
        if not self.api_key:
            self.logger.error("HasData API Key 未配置")
            return []

        semaphore = self._get_semaphore()

        async with semaphore:
            self.logger.info(f"执行 Google 搜索: query={query}, max_results={max_results}")

            try:
                params = {
                    "q": query,
                    "hl": language,
                    "start": 0
                }
                if location:
                    params["location"] = location
                if tbs:
                    params["tbs"] = tbs

                async with httpx.AsyncClient(timeout=self.TIMEOUT_SECONDS) as client:
                    response = await client.get(
                        self.GOOGLE_LIGHT_SERP_URL,
                        params=params,
                        headers=self._get_headers()
                    )
                    response.raise_for_status()
                    data = response.json()

                # 检查状态
                metadata = data.get("requestMetadata", {})
                if metadata.get("status") != "ok":
                    self.logger.warning(f"Google SERP API 返回状态异常: {metadata}")
                    return []

                # 解析结果
                results = []
                organic_results = data.get("organicResults", [])

                for item in organic_results[:max_results]:
                    results.append(SerpResult(
                        url=item.get("link", ""),
                        title=item.get("title", ""),
                        description=item.get("snippet", ""),
                        raw_content=item.get("snippet", "")  # 初始内容为摘要
                    ))

                self.logger.info(f"Google 搜索完成: 获取 {len(results)} 条结果")
                return results

            except httpx.HTTPStatusError as e:
                self._handle_http_error(e, query)
                return []
            except Exception as e:
                self.logger.error(f"Google 搜索异常: {e}")
                return []

    async def scrape_web(
        self,
        url: str,
        js_rendering: bool = True,
        wait: int = 3000,
        block_resources: bool = True
    ) -> Optional[ScrapeResult]:
        """
        Web Scrape 网页抓取

        Args:
            url: 目标 URL
            js_rendering: 是否启用 JS 渲染
            wait: 等待时间 (ms)
            block_resources: 是否阻止加载静态资源

        Returns:
            抓取结果
        """
        if not self.api_key:
            self.logger.error("HasData API Key 未配置")
            return None

        semaphore = self._get_semaphore()

        async with semaphore:
            self.logger.info(f"执行网页抓取: url={url}")

            try:
                request_body = {
                    "url": url,
                    "jsRendering": js_rendering,
                    "wait": wait,
                    "blockResources": block_resources,
                    "outputFormat": ["text", "html"]
                }

                async with httpx.AsyncClient(timeout=self.TIMEOUT_SECONDS) as client:
                    response = await client.post(
                        self.WEB_SCRAPE_URL,
                        json=request_body,
                        headers=self._get_headers()
                    )
                    response.raise_for_status()
                    data = response.json()

                # 检查状态
                metadata = data.get("requestMetadata", {})
                if metadata.get("status") != "ok":
                    self.logger.warning(f"Web Scrape API 返回状态异常: {metadata}")
                    return None

                # 提取标题 (从 HTML 中简单提取)
                html_content = data.get("content", "")
                title = self._extract_title(html_content)

                result = ScrapeResult(
                    url=url,
                    content=data.get("text", ""),
                    title=title,
                    image_urls=[]
                )

                self.logger.info(f"网页抓取完成: url={url}, content_length={len(result.content)}")
                return result

            except httpx.HTTPStatusError as e:
                self._handle_http_error_for_url(e, url)
                return None
            except Exception as e:
                self.logger.error(f"网页抓取异常: {e}")
                return None

    def _extract_title(self, html: str) -> str:
        """从 HTML 中提取标题"""
        try:
            import re
            match = re.search(r'<title[^>]*>([^<]+)</title>', html, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        except Exception:
            pass
        return ""

    def _handle_http_error(self, e: httpx.HTTPStatusError, query: str):
        """处理 HTTP 错误"""
        status_code = e.response.status_code
        if status_code == 429:
            self.logger.error(f"请求频率超限: query={query}")
        elif status_code == 403:
            self.logger.error(f"API Key 无效或额度用完: query={query}")
        else:
            self.logger.error(f"HTTP 请求失败 [{status_code}]: query={query}")

    def _handle_http_error_for_url(self, e: httpx.HTTPStatusError, url: str):
        """处理 HTTP 错误 (URL)"""
        status_code = e.response.status_code
        if status_code == 429:
            self.logger.error(f"请求频率超限: url={url}")
        elif status_code == 403:
            self.logger.error(f"API Key 无效或额度用完: url={url}")
        else:
            self.logger.error(f"HTTP 请求失败 [{status_code}]: url={url}")


# 单例
hasdata_service = HasDataService()
