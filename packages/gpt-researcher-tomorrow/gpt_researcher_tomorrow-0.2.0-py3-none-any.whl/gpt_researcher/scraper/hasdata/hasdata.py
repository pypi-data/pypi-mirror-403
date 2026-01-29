"""
HasData 爬虫 - 使用 HasData Web Scrape API

用于 GPT Researcher 的网页抓取功能
"""
import asyncio
import logging
from typing import Tuple, List


class HasDataScraper:
    """
    HasData 爬虫，调用 HasData Web Scrape API

    返回格式: (content: str, image_urls: List[str], title: str)
    """

    def __init__(self, url: str, session=None):
        """
        初始化爬虫

        Args:
            url: 要抓取的 URL
            session: HTTP session（可选，保持兼容性，不使用）
        """
        self.url = url
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"HasDataScraper 初始化: url={url}")

    async def scrape_async(self) -> Tuple[str, List[str], str]:
        """
        异步抓取方法（GPT Researcher 优先调用此方法）

        Returns:
            (content, image_urls, title) 元组
        """
        return await self._async_scrape()

    async def _async_scrape(self) -> Tuple[str, List[str], str]:
        """
        执行异步抓取

        Returns:
            (content, image_urls, title) 元组
        """
        from gpt_researcher.utils.hasdata_service import hasdata_service

        self.logger.info(f"🔥 HasDataScraper._async_scrape 开始执行: url={self.url}")

        try:
            # 调用 HasData 抓取
            self.logger.info(f"🌐 调用 HasData API 抓取: url={self.url}")
            result = await hasdata_service.scrape_web(
                url=self.url,
                js_rendering=True,
                wait=3000,
                block_resources=True
            )

            if result is None:
                self.logger.warning(f"⚠️ HasDataScraper 抓取失败 (result=None): url={self.url}")
                return "", [], ""

            self.logger.info(f"✅ HasDataScraper 抓取完成: url={self.url}, content_length={len(result.content)}, title={result.title}")
            return result.content, result.image_urls, result.title

        except Exception as e:
            import traceback
            self.logger.error(f"❌ HasDataScraper 抓取异常: url={self.url}, error={e}")
            self.logger.error(traceback.format_exc())
            return "", [], ""
