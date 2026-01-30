from gpt_researcher.utils.workers import WorkerPool

from ..actions.utils import stream_output
from ..actions.web_scraping import scrape_urls
from ..scraper.utils import get_image_hash


class BrowserManager:
    """Manages context for the researcher agent."""

    def __init__(self, researcher):
        self.researcher = researcher
        self.worker_pool = WorkerPool(
            researcher.cfg.max_scraper_workers,
            researcher.cfg.scraper_rate_limit_delay
        )

    async def browse_urls(self, urls: list[str]) -> list[dict]:
        """
        Scrape content from a list of URLs.

        Args:
            urls (list[str]): list of URLs to scrape.

        Returns:
            list[dict]: list of scraped content results.
        """
        if self.researcher.verbose:
            await stream_output(
                "logs",
                "scraping_urls",
                f"🌐 Scraping content from {len(urls)} URLs...",
                self.researcher.websocket,
            )

        scraped_content, images = await scrape_urls(
            urls, self.researcher.cfg, self.worker_pool
        )
        self.researcher.add_research_sources(scraped_content)

        # 为每个成功抓取的页面发送单独的 scraping 事件
        if self.researcher.verbose:
            for item in scraped_content:
                if item.get('raw_content'):
                    await stream_output(
                        "scraping",
                        item.get('url', ''),
                        item.get('raw_content', '')[:200],  # 发送前200个字符作为预览
                        self.researcher.websocket,
                        True,
                        {
                            "url": item.get('url', ''),
                            "title": item.get('title', ''),
                        }
                    )

        new_images = self.select_top_images(images, k=4)  # Select top 4 images
        self.researcher.add_research_images(new_images)

        if self.researcher.verbose:
            await stream_output(
                "logs",
                "scraping_content",
                f"📄 Scraped {len(scraped_content)} pages of content",
                self.researcher.websocket,
            )
            await stream_output(
                "logs",
                "scraping_images",
                f"🖼️ Selected {len(new_images)} new images from {len(images)} total images",
                self.researcher.websocket,
                True,
                new_images,
            )
            await stream_output(
                "logs",
                "scraping_complete",
                f"🌐 Scraping complete",
                self.researcher.websocket,
            )

        return scraped_content

    def select_top_images(self, images: list[dict], k: int = 2) -> list[str]:
        """
        Select most relevant images and remove duplicates based on image content.

        Args:
            images (list[dict]): list of image dictionaries with 'url' and 'score' keys.
            k (int): Number of top images to select if no high-score images are found.

        Returns:
            list[str]: list of selected image URLs.
        """
        unique_images = []
        seen_hashes = set()
        current_research_images = self.researcher.get_research_images()

        # Process images in descending order of their scores
        for img in sorted(images, key=lambda im: im["score"], reverse=True):
            img_hash = get_image_hash(img['url'])
            if (
                img_hash
                and img_hash not in seen_hashes
                and img['url'] not in current_research_images
            ):
                seen_hashes.add(img_hash)
                unique_images.append(img["url"])

                if len(unique_images) == k:
                    break

        return unique_images
