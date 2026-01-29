"""
HasData 检索器 - 使用 HasData Google SERP API

用于 GPT Researcher 的搜索功能
"""
import asyncio
import logging
from typing import Any, Dict, List, Optional


class HasDataRetriever:
    """
    HasData 检索器，调用 HasData Google Light SERP API

    返回格式符合 gpt-researcher 要求:
    [
        {"href": "http://example.com/page1"},
        {"href": "http://example.com/page2"}
    ]
    """

    def __init__(self, query: str, query_domains: Optional[List[str]] = None):
        """
        初始化检索器

        Args:
            query: 搜索查询
            query_domains: 限定搜索的域名列表（可选，暂不支持）
        """
        self.query = query
        self.query_domains = query_domains or []
        self.logger = logging.getLogger(__name__)

    async def asearch(self, max_results: int = 10) -> Optional[List[Dict[str, Any]]]:
        """
        异步搜索方法（GPT Researcher 优先调用此方法）

        Args:
            max_results: 最大返回结果数

        Returns:
            搜索结果列表
        """
        return await self._async_search(max_results)

    async def _async_search(self, max_results: int) -> List[Dict[str, Any]]:
        """
        执行异步搜索

        Args:
            max_results: 最大返回结果数

        Returns:
            搜索结果列表
        """
        from gpt_researcher.utils.hasdata_service import hasdata_service

        self.logger.info(f"HasDataRetriever 执行搜索: query={self.query}, max_results={max_results}")

        try:
            # 调用 HasData 搜索
            results = await hasdata_service.search_google(
                query=self.query,
                max_results=max_results
            )

            # 转换为 GPT Researcher 需要的格式
            # 注意: GPT Researcher 在 _search_relevant_source_urls 中使用 url.get("href") 提取URL
            # 重要: 不要包含 raw_content 字段,否则 GPT Researcher 会跳过爬取步骤
            formatted_results = []
            for item in results:
                formatted_results.append({
                    "href": item.url,  # 使用 "href" 而不是 "url"
                    # 不包含 raw_content,让 GPT Researcher 进行爬取
                })

            self.logger.info(f"HasDataRetriever 搜索完成: 获取 {len(formatted_results)} 条结果")

            # 调试：打印前3个URL
            if formatted_results:
                urls = [r.get('href') for r in formatted_results[:3]]
                self.logger.info(f"HasDataRetriever 返回的URL示例: {urls}")

            return formatted_results

        except Exception as e:
            self.logger.error(f"HasDataRetriever 搜索异常: {e}")
            return []

    def search(self, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        同步搜索方法（GPT Researcher 可能调用此方法）

        Args:
            max_results: 最大返回结果数

        Returns:
            搜索结果列表
        """
        self.logger.info(f"HasDataRetriever.search() 被调用: query={self.query}, max_results={max_results}")

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 如果事件循环已在运行，创建新任务
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self._async_search(max_results))
                    result = future.result()
                    self.logger.info(f"HasDataRetriever.search() 完成: 返回 {len(result)} 条结果")
                    return result
            else:
                result = loop.run_until_complete(self._async_search(max_results))
                self.logger.info(f"HasDataRetriever.search() 完成: 返回 {len(result)} 条结果")
                return result
        except RuntimeError:
            # 没有事件循环时创建新的
            result = asyncio.run(self._async_search(max_results))
            self.logger.info(f"HasDataRetriever.search() 完成: 返回 {len(result)} 条结果")
            return result
        except Exception as e:
            self.logger.error(f"HasDataRetriever.search() 异常: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return []
