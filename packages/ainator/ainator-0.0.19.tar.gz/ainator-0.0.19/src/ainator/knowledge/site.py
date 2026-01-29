"""
Website → RAG knowledge base using custom crawler + LlamaIndex + LanceDB
"""

import asyncio
import re
import functools
import unicodedata
from urllib.parse import urljoin, urlparse

import cli2
import httpx
from parsel import Selector

from llama_index.core import (
    Document,
    VectorStoreIndex,
    StorageContext,
    Settings,
)

from llama_index.core.ingestion import IngestionPipeline
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.postprocessor import SimilarityPostprocessor
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.lancedb import LanceDBVectorStore

from agno.vectordb.llamaindex import LlamaIndexVectorDb
from agno.knowledge.knowledge import Knowledge


def slugify(value: str, separator: str = "-", max_length: int | None = None) -> str:
    value = unicodedata.normalize('NFKD', value)
    value = value.encode('ascii', 'ignore').decode('ascii')
    value = value.lower().strip()
    value = re.sub(r'[\W_]+', separator, value)
    value = value.strip(separator)
    if max_length:
        value = value[:max_length].rstrip(separator)
    return value


# ──────────────────────────────────────────────────────────────────────────────
# Crawler (unchanged from previous version — kept your cli2.Queue style)
# ──────────────────────────────────────────────────────────────────────────────

class FastWebsiteCrawler:
    def __init__(
        self,
        max_links: int = 30,
        max_concurrent: int = 6,
        max_depth: int = 4,
        follow_same_domain_only: bool = True,
        timeout: float = 20.0,
        user_agent: str = "Mozilla/5.0 (compatible; FastWebsiteCrawler/1.0)",
        retry_attempts: int = 3,
    ):
        self.max_links = max_links
        self.max_concurrent = max_concurrent
        self.max_depth = max_depth
        self.follow_same_domain_only = follow_same_domain_only
        self.timeout = timeout
        self.user_agent = user_agent
        self.retry_attempts = retry_attempts

    async def crawl(self, start_url: str) -> list[Document]:
        base_domain = urlparse(start_url).netloc
        visited = set()
        results: list[Document] = []

        page_queue = cli2.Queue(num_workers=self.max_concurrent)
        await page_queue.put((start_url, 0))

        async def worker():
            client = httpx.AsyncClient(
                headers={"User-Agent": self.user_agent},
                timeout=httpx.Timeout(self.timeout),
                follow_redirects=True,
                http2=True,
            )
            try:
                while True:
                    url, depth = await page_queue.get()
                    if url in visited or len(visited) >= self.max_links or depth > self.max_depth:
                        page_queue.task_done()
                        continue

                    visited.add(url)
                    cli2.log.info("Processing %s (depth %d, visited %d)", url, depth, len(visited))

                    text = None
                    for attempt in range(1, self.retry_attempts + 1):
                        try:
                            resp = await client.get(url)
                            resp.raise_for_status()
                            html = resp.text
                            break
                        except Exception as e:
                            cli2.log.warning("Fetch failed %s attempt %d/%d: %s", url, attempt, self.retry_attempts, e)
                            if attempt == self.retry_attempts:
                                html = None
                            await asyncio.sleep(1.5 ** attempt)

                    if not html:
                        page_queue.task_done()
                        continue

                    sel = Selector(html)
                    main_sel = sel.css("div.body, article, div[role='main'], main, .document") or sel
                    text_parts = main_sel.xpath(".//text()").getall()
                    text = " ".join(t.strip() for t in text_parts if t.strip())
                    text = re.sub(r'\s+', ' ', text).strip()

                    if len(text) < 150:
                        text = " ".join(sel.xpath("//text()").getall())
                        text = re.sub(r'\s+', ' ', text).strip()

                    if len(text) < 80:
                        cli2.log.debug("Skipping short page %s (%d chars)", url, len(text))
                        page_queue.task_done()
                        continue

                    doc = Document(
                        text=text,
                        metadata={
                            "url": url,
                            "depth": depth,
                            "source": "website",
                            "domain": base_domain,
                        },
                    )
                    results.append(doc)

                    for href in sel.xpath("//a/@href").getall():
                        abs_url = urljoin(url, href.strip())
                        p = urlparse(abs_url)
                        if p.scheme not in ("http", "https"):
                            continue
                        if self.follow_same_domain_only and p.netloc != base_domain:
                            continue
                        if re.search(r'\.(pdf|jpg|png|zip|docx?)$', abs_url, re.I):
                            continue
                        if abs_url not in visited:
                            await page_queue.put((abs_url, depth + 1))

                    page_queue.task_done()

            finally:
                await client.aclose()

        workers = [asyncio.create_task(worker()) for _ in range(self.max_concurrent)]
        await page_queue.join()
        for w in workers:
            w.cancel()
        await asyncio.gather(*workers, return_exceptions=True)

        cli2.log.info("Crawl done → %d documents, %d urls visited", len(results), len(visited))
        return results


# ──────────────────────────────────────────────────────────────────────────────
# Main Knowledge Class
# ──────────────────────────────────────────────────────────────────────────────

class SiteKnowledge:
    """Website scraper / RAG knowledge base"""

    def __init__(self, configuration):
        self.configuration = configuration

    @functools.cached_property
    def embed_model(self):
        from llama_index.embeddings.huggingface import HuggingFaceEmbedding
        return HuggingFaceEmbedding(
            model_name="BAAI/bge-small-en-v1.5",
            local_files_only=self.configuration.get('airgap', False),
        )

    def _get_persist_dir(self, slug: str):
        return self.configuration.path / f'rag_{slug}'

    def get(self, base_url: str, **kwargs):
        """
        Retrieve the Knowledge object for a previously ingested site (by slug).
        Compatible with your system's usage pattern.
        """
        slug = slugify(re.sub(r'^https?://', '', base_url.rstrip('/')))
        persist_dir = self._get_persist_dir(slug)

        if not persist_dir.exists():
            raise ValueError(f"No ingested site found for slug '{slug}' at {persist_dir}")

        vector_store = LanceDBVectorStore(
            uri=str(persist_dir),
            table_name="website_index",
        )

        index = VectorStoreIndex.from_vector_store(
            vector_store=vector_store,
            embed_model=self.embed_model,
        )

        retriever = VectorIndexRetriever(
            index=index,
            similarity_top_k=kwargs.get("similarity_top_k", 4),
            node_postprocessors=[
                SimilarityPostprocessor(
                    similarity_cutoff=kwargs.get("similarity_cutoff", 0.76)
                )
            ],
        )

        vector_db = LlamaIndexVectorDb(knowledge_retriever=retriever)

        base_url = self.configuration['knowledge'].get(slug, {}).get('base_url', 'unknown')

        return Knowledge(
            name=f"Website: {slug}",
            description=f"Content scraped from {base_url}",
            vector_db=vector_db,
        )

    @cli2.cmd
    async def add(
        self,
        base_url: str,
        max_depth: int = 3,
        max_links: int = 25,
        max_concurrent: int = 8,
    ):
        slug = slugify(re.sub(r'^https?://', '', base_url.rstrip('/')))

        with self.configuration:
            self.configuration['knowledge'][slug] = dict(
                plugin='site',
                base_url=base_url,
            )

        persist_dir = self._get_persist_dir(slug)

        cli2.log.info("Starting website ingestion → %s (slug: %s)", base_url, slug)

        Settings.embed_model = self.embed_model

        crawler = FastWebsiteCrawler(
            max_links=max_links,
            max_concurrent=max_concurrent,
            max_depth=max_depth,
            follow_same_domain_only=True,
        )

        raw_docs = await crawler.crawl(base_url)

        if not raw_docs:
            cli2.log.error("No usable content crawled.")
            return

        chunker = SentenceSplitter(
            chunk_size=900,
            chunk_overlap=180,
        )

        pipeline = IngestionPipeline(transformations=[chunker])

        nodes = await pipeline.arun(documents=raw_docs, show_progress=True)

        vector_store = LanceDBVectorStore(
            uri=str(persist_dir),
            table_name="website_index",
        )

        storage_context = StorageContext.from_defaults(vector_store=vector_store)

        index = VectorStoreIndex(
            nodes=nodes,
            storage_context=storage_context,
            embed_model=self.embed_model,
            show_progress=True,
        )

        storage_context.persist(persist_dir=str(persist_dir))

        cli2.log.info("Ingestion completed for %s (slug: %s)", base_url, slug)
