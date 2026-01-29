""" Code knowledge module """
import cli2
import functools
from pathlib import Path


class CodeKnowledge:
    """
    Manage code repositories in RAG
    """

    def __init__(self, configuration):
        self.configuration = configuration

    @functools.cached_property
    def embed_model(self):
        from llama_index.embeddings.huggingface import HuggingFaceEmbedding
        return HuggingFaceEmbedding(
            model_name="BAAI/bge-small-en-v1.5",  # fast + good for code/docs
            local_files_only=self.configuration.get('airgap', False),
        )

    def get(self, path, **kwargs):
        path = Path(path)
        persist_dir = self.configuration.path / f'rag_{path.name}'
        table_name = "code_repo_index"

        from llama_index.vector_stores.lancedb import LanceDBVectorStore
        vector_store = LanceDBVectorStore(
            uri=str(persist_dir),
            table_name=table_name,
        )

        from llama_index.core import VectorStoreIndex
        index = VectorStoreIndex.from_vector_store(
            vector_store=vector_store,
            embed_model=self.embed_model,
        )

        from llama_index.core.retrievers import VectorIndexRetriever
        from llama_index.core.postprocessor import SimilarityPostprocessor
        retriever = VectorIndexRetriever(
            index=index,
            similarity_top_k=3,          # how many chunks to retrieve (tune this)
            node_postprocessors=[
                SimilarityPostprocessor(similarity_cutoff=0.78)   # 0.75–0.82 common range
            ],
            # Optional: add filters on metadata, e.g.
            # node_postprocessors=[MetadataReplacementPostProcessor(...)],
            # similarity_cutoff=0.75,
        )

        from agno.vectordb.llamaindex import LlamaIndexVectorDb
        vector_db = LlamaIndexVectorDb(knowledge_retriever=retriever)

        from agno.knowledge.knowledge import Knowledge
        return Knowledge(
            name=f'{path} code repository',
            description=f'Code and documentation',
            vector_db=vector_db,
        )

    @cli2.cmd
    async def add(self, path, language="python", num_workers=12):
        """
        Add a code repository into the rag.

        :param path: Path to the code repository to load
        """
        path = Path(path).resolve().absolute()
        with self.configuration:
            self.configuration['knowledge'][path.name] = dict(
                plugin='code',
                path=path,
            )

        rag_path = self.configuration.path / f'rag_{path.name}'

        repo_path = Path(path).expanduser().resolve()
        if not repo_path.is_dir():
            print(f"Error: {repo_path} is not a directory")
            return
        print(f"Embedding repo: {repo_path} (using {num_workers} workers)")

        import warnings
        warnings.filterwarnings(
            "ignore",
            message="Removing unpickleable private attribute",
            category=UserWarning,
        )

        # 2. Code-aware splitter (tree-sitter based)
        from llama_index.core.node_parser import CodeSplitter
        code_splitter = CodeSplitter(
            language=language,
            chunk_lines=80,
            chunk_lines_overlap=20,
            max_chars=1500,
        )

        # 3. Hierarchical parser (large → medium → small chunks)
        from llama_index.core.node_parser import HierarchicalNodeParser, SentenceSplitter
        hierarchical_parser = HierarchicalNodeParser.from_defaults(
            node_parser_ids=["default", "default", "code"],
            node_parser_map={
                "default": SentenceSplitter(
                    chunk_size=1024,
                    chunk_overlap=150,
                ),
                "code": code_splitter,
            },
            chunk_overlap=150,
        )

        # 4. Reader with parallel loading
        from llama_index.core import SimpleDirectoryReader
        reader = SimpleDirectoryReader(
            input_dir=repo_path,
            recursive=True,
            required_exts=[
                ".py", ".js", ".ts", ".jsx", ".tsx", ".go", ".rs", ".java",
                ".cpp", ".c", ".h", ".md", ".rst", ".txt", ".yaml", ".yml",
                ".toml", ".json", ".sql",
            ],
            exclude=[
                "node_modules", "venv", ".git", "__pycache__", "target",
                "dist", "build", "*.min.js", "*.min.css", "*.pyc", "*.log"
            ],
            filename_as_id=True,
        )

        print("Loading documents in parallel...")
        documents = reader.load_data(num_workers=num_workers)

        # 5. Add custom metadata serially
        print("Adding custom metadata...")
        import os
        for doc in documents:
            rel_path = os.path.relpath(doc.metadata["file_path"], repo_path)
            doc.metadata["file_path_relative"] = rel_path
            doc.metadata["repo_name"] = repo_path.name

        # 6. Setup LanceDB vector store
        from llama_index.vector_stores.lancedb import LanceDBVectorStore
        from llama_index.core import StorageContext, VectorStoreIndex, load_index_from_storage

        persist_path = Path(rag_path)
        persist_path.mkdir(parents=True, exist_ok=True)

        vector_store = LanceDBVectorStore(
            uri=str(persist_path),           # folder on disk
            table_name="code_repo_index",    # can be fixed or dynamic per repo
        )

        storage_context = StorageContext.from_defaults(vector_store=vector_store)

        # 7. Index creation / loading
        if (persist_path / "code_repo_index").exists():  # LanceDB creates a subfolder/table dir
            print("Loading existing LanceDB index...")
            index = load_index_from_storage(storage_context)
            # Optional: incremental add (if you want to update with new nodes)
            # new_nodes = ... parse new docs ...
            # index.insert_nodes(new_nodes)
        else:
            print("Creating new LanceDB vector index...")
            # Ingestion pipeline for parsing
            from llama_index.core.ingestion import IngestionPipeline
            pipeline = IngestionPipeline(
                transformations=[
                    hierarchical_parser,
                ]
            )
            print("Parsing & transforming nodes in parallel...")
            nodes = await pipeline.arun(
                documents=documents,
                num_workers=num_workers,
                show_progress=True
            )
            print(f"→ Parsed {len(nodes)} nodes")

            index = VectorStoreIndex(
                nodes,
                storage_context=storage_context,
                embed_model=self.embed_model,
            )
            persist_dir = rag_path
            # LanceDB persists automatically on creation/insert, but explicit persist for safety
            storage_context.persist(persist_dir=str(persist_path))
            print(f"Index saved to LanceDB at {persist_dir}")

        print("Done! Repo is now indexed in LanceDB and ready for querying.")
