from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_text_splitters import MarkdownHeaderTextSplitter

class DocumentChunker:
  @staticmethod
  def chunk(documents: list[Document], chucking_method: str = "recursive", chunk_size: int=3_000, chunk_overlap: int=300) -> list[Document]:
      if chucking_method == "recursive":
        return DocumentChunker.chunk_recursive(documents, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
      elif chucking_method == "markdownHeader":
        return DocumentChunker.chunk_markdown(documents, chunk_size=chunk_size, chunk_overlap=chunk_overlap)

  @staticmethod
  def chunk_recursive(documents: list[Document], chunk_size: int=3_000, chunk_overlap: int=300) -> list[Document]:
        """
        Recursively split documents into smaller chunks while preserving metadata.

        This function takes a list of documents and splits them into smaller chunks using
        RecursiveCharacterTextSplitter. Documents smaller than the chunk size are kept intact,
        while larger documents are split into multiple chunks with overlapping content.

        Args:
            documents (list[Document]): A list of Document objects to be chunked.
            chunk_size (int, optional): The maximum size of each chunk in characters.
                Defaults to 3,000.

        Returns:
            list[Document]: A list of Document objects where each document's content is
                at most chunk_size characters. Each chunk preserves the metadata from
                its original document.

        Notes:
            - Chunk overlap is automatically set to 10% of the chunk_size to maintain
              context between chunks.
            - Documents smaller than or equal to chunk_size are returned unchanged.
            - Metadata from the original document is copied to all resulting chunks.
        """
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=int(chunk_size//10))
        chunked_documents = []
        for doc in documents:
            if len(doc.page_content) <= chunk_size:
                chunked_documents.append(doc)
                continue
            chunks = text_splitter.split_text(doc.page_content)
            for chunk in chunks:
                chunked_documents.append(
                    Document(page_content=chunk, metadata=doc.metadata)
                )
        return chunked_documents

  @staticmethod
  def chunk_token(documents: list[Document], max_tokens: int=1_000) -> list[Document]:
        """
        Splits a list of documents into smaller chunks based on token count.

        This function takes a list of Document objects and splits them into smaller chunks
        using a recursive character text splitter based on tiktoken encoding. Each chunk
        respects the maximum token limit while maintaining some overlap between consecutive
        chunks for context preservation.

        Args:
            documents (list[Document]): A list of Document objects to be chunked. Each Document
                should have 'page_content' (str) and 'metadata' (dict) attributes.
            max_tokens (int, optional): The maximum number of tokens allowed per chunk.
                Defaults to 1,000. The chunk overlap is automatically set to 10% of this value.

        Returns:
            list[Document]: A list of new Document objects where each document represents a chunk
                of the original documents. Each chunked Document preserves the metadata from its
                source document.

        Note:
            - Uses the "cl100k_base" tiktoken encoding (commonly used for GPT-4 and similar models)
            - Chunk overlap is set to max_tokens // 10 to maintain context between chunks
            - Original document metadata is preserved in all generated chunks
        """
        text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(encoding_name="cl100k_base",chunk_size=max_tokens, chunk_overlap=max_tokens//10)
        chunked_documents = []
        for doc in documents:
            chunks = text_splitter.split_text(doc.page_content)
            for chunk in chunks:
                chunked_documents.append(
                    Document(page_content=chunk, metadata=doc.metadata)
                )
        return chunked_documents

  @staticmethod
  def chunk_markdown(documents: list[Document], chunk_size: int=3_000, chunk_overlap: int=300) -> list[Document]:
        """
        Splits markdown documents based on headers and then into smaller chunks.

        This function takes a list of Document objects containing markdown content and splits
        them based on markdown headers (# H1, ## H2, ### H3, etc.). After splitting by headers,
        it further chunks large sections using RecursiveCharacterTextSplitter to ensure no
        chunk exceeds the specified size.

        Args:
            documents (list[Document]): A list of Document objects with markdown content.
            chunk_size (int, optional): The maximum size of each chunk in characters.
                Defaults to 3,000.

        Returns:
            list[Document]: A list of Document objects where each document represents a chunk.
                Metadata includes the markdown header hierarchy and original document metadata.

        Note:
            - Headers are split at levels: H1 (#), H2 (##), and H3 (###)
            - Header information is preserved in the metadata
            - Large sections are further split to respect chunk_size limit
            - Chunk overlap is set to 10% of chunk_size for context preservation
        """
        # Define headers to split on
        headers_to_split_on = [
            ("#", "h1"),
            ("##", "h2"),
            ("###", "h3"),
            ("####", "h4"),
        ]

        markdown_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=headers_to_split_on,
            strip_headers=False
        )

        # Secondary splitter for large sections
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )

        chunked_documents = []
        for doc in documents:
            # First split by markdown headers
            md_chunks = markdown_splitter.split_text(doc.page_content)

            # Then split large sections if needed
            for md_chunk in md_chunks:
                # Merge metadata from original doc and header metadata
                merged_metadata = {**doc.metadata, **md_chunk.metadata}
                if len(md_chunk.page_content) <= chunk_size:
                    chunked_documents.append(
                        Document(page_content=md_chunk.page_content, metadata=merged_metadata)
                    )
                else:
                    # Further split large sections
                    sub_chunks = text_splitter.split_text(md_chunk.page_content)
                    for sub_chunk in sub_chunks:
                        chunked_documents.append(
                            Document(page_content=sub_chunk, metadata=merged_metadata)
                        )

        return chunked_documents
