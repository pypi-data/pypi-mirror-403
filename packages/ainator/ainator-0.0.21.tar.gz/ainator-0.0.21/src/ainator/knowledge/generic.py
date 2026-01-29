""" Generic knowledge module """
import cli2
import functools
import os
from pathlib import Path
from typing import List


class GenericKnowledge:
    """
    Manage generic directories in RAG with include/exclude filters
    """

    def __init__(self, configuration):
        self.configuration = configuration

    @functools.cached_property
    def embed_model(self):
        from llama_index.embeddings.huggingface import HuggingFaceEmbedding
        return HuggingFaceEmbedding(
            model_name="BAAI/bge-small-en-v1.5",
            local_files_only=self.configuration.get('airgap', False),
        )

    def _get_persist_dir(self, slug: str) -> Path:
        return self.configuration.path / f'rag_{slug}'

    def get(self, path: str, **kwargs):
        path = Path(path)
        persist_dir = self._get_persist_dir(path.name)

        if not persist_dir.exists():
            raise ValueError(f"No generic knowledge found for slug '{path.name}' at {persist_dir}")

        from llama_index.core import VectorStoreIndex
        from llama_index.vector_stores.lancedb import LanceDBVectorStore
        from llama_index.core.retrievers import VectorIndexRetriever
        from llama_index.core.postprocessor import SimilarityPostprocessor
        from agno.vectordb.llamaindex import LlamaIndexVectorDb
        from agno.knowledge.knowledge import Knowledge

        vector_store = LanceDBVectorStore(
            uri=str(persist_dir),
            table_name="generic_index",
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

        return Knowledge(
            name=f"Search files in directory {path.name}",
            description="\n".join([path.name for path in path.iterdir()]),
            vector_db=vector_db,
        )

    @cli2.cmd
    async def add(
        self,
        path: str,
        include: List[str] | None = None,
        exclude: List[str] | None = None,
        num_workers: int = 8,
    ):
        path = Path(path).resolve().absolute()
        if not path.exists():
            cli2.log.error(f"Path does not exist: {path}")
            return

        with self.configuration:
            self.configuration['knowledge'][path.name] = dict(
                plugin='generic',
                path=str(path),
            )

        if not path.is_dir():
            cli2.log.warning(f"Path is not a directory, treating as single file dir: {path}")
            input_dir = path.parent
        else:
            input_dir = path

        persist_path = self._get_persist_dir(path.name)
        persist_path.mkdir(parents=True, exist_ok=True)

        cli2.log.info(f"Ingestion generic → slug: {path.name}, path: {path}")

        from llama_index.core import (
            SimpleDirectoryReader,
            StorageContext,
            VectorStoreIndex,
            load_index_from_storage,
        )
        from llama_index.core.node_parser import SentenceSplitter
        from llama_index.core.ingestion import IngestionPipeline
        from llama_index.core.ingestion import IngestionPipeline
        from llama_index.vector_stores.lancedb import LanceDBVectorStore
        vector_store = LanceDBVectorStore(
            uri=str(persist_path),
            table_name="generic_index",
        )
        storage_context = StorageContext.from_defaults(vector_store=vector_store)

        index = None
        try:
            index = load_index_from_storage(
                storage_context,
                embed_model=self.embed_model,
            )
            cli2.log.info(" ✓ Loaded existing index (will add new nodes)")
        except Exception:
            cli2.log.info("Creating new index")

        reader = SimpleDirectoryReader(
            input_dir=input_dir,
            required_exts=include,
            exclude=exclude or [],
            recursive=True,
            exclude_hidden=True,
            filename_as_id=True,
        )

        documents = reader.load_data(num_workers=num_workers)
        if not documents:
            cli2.log.warning("No documents found")
            return

        for doc in documents:
            rel_path = os.path.relpath(doc.metadata["file_path"], input_dir)
            doc.metadata["file_path_relative"] = rel_path

        splitter = SentenceSplitter(chunk_size=1024, chunk_overlap=150)

        pipeline = IngestionPipeline(transformations=[splitter])

        nodes = await pipeline.arun(documents=documents, num_workers=num_workers, show_progress=True)
        cli2.log.info(f" → {len(nodes)} nodes parsed")

        if index is None:
            index = VectorStoreIndex(
                nodes,
                storage_context=storage_context,
                embed_model=self.embed_model,
                show_progress=True,
            )
        else:
            index.insert_nodes(nodes)

        storage_context.persist(persist_dir=str(persist_path))

        cli2.log.info(f" ✓ Generic knowledge '{path.name}' ready!")
