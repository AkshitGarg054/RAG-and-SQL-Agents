import os
import yaml
from pyprojroot import here
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from dotenv import load_dotenv


class PrepareVectorDB:
    """
    A class to prepare and manage a Vector Database (VectorDB) using documents from a specified directory.
    The class performs the following tasks:
    - Loads and splits documents (PDFs).
    - Splits the text into chunks based on the specified chunk size and overlap.
    - Embeds the document chunks using a specified embedding model.
    - Stores the embedded vectors in a persistent VectorDB directory.

    Attributes:
        doc_dir (str): Path to the directory containing documents (PDFs) to be processed.
        chunk_size (int): The maximum size of each chunk (in characters) into which the document text will be split.
        chunk_overlap (int): The number of overlapping characters between consecutive chunks.
        embedding_model (str): The name of the embedding model to be used for generating vector representations of text.
        vectordb_dir (str): Directory where the resulting vector database will be stored.
        collection_name (str): The name of the collection to be used within the vector database.

    Methods:
        path_maker(file_name: str, doc_dir: str) -> str:
            Creates a full file path by joining the given directory and file name.

        run() -> None:
            Executes the process of reading documents, splitting text, embedding them into vectors, and 
            saving the resulting vector database. If the vector database directory already exists, it skips
            the creation process.
    """

    def __init__(self,
                 doc_dir: str,
                 chunk_size: int,
                 chunk_overlap: int,
                 embedding_model: str,
                 vectordb_dir: str,
                 collection_name: str
                 ) -> None:

        self.doc_dir = doc_dir
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.embedding_model = embedding_model
        self.vectordb_dir = vectordb_dir
        self.collection_name = collection_name

    def path_maker(self, file_name: str, doc_dir):
        """
        Creates a full file path by joining the provided directory and file name.

        Args:
            file_name (str): Name of the file.
            doc_dir (str): Path of the directory.

        Returns:
            str: Full path of the file.
        """
        return os.path.join(here(doc_dir), file_name)

    def run(self):
        """
        Executes the main logic to create and store document embeddings in a VectorDB.

        It incrementally updates the database:
        - Connects to the VectorDB.
        - Checks existing document metadata to see which PDFs are already indexed.
        - Loads only new PDF documents from the `doc_dir`.
        - Splits and embeds the new chunks.
        - Adds them to the database in batches.
        """
        import time
        if not os.path.exists(here(self.vectordb_dir)):
            os.makedirs(here(self.vectordb_dir))
            print(f"Directory '{self.vectordb_dir}' was created.")
            
        vectordb = Chroma(
            collection_name=self.collection_name,
            embedding_function=GoogleGenerativeAIEmbeddings(model=self.embedding_model),
            persist_directory=str(here(self.vectordb_dir))
        )
        
        # 1. Fetch existing sources from the vector database to avoid re-embedding
        existing_data = vectordb.get(include=["metadatas"])
        existing_sources = set()
        for metadata in existing_data.get("metadatas", []):
            if "source" in metadata:
                # normalize path to avoid mismatch on different OS
                existing_sources.add(os.path.normpath(metadata["source"]))

        # 2. Check which files are new
        file_list = os.listdir(here(self.doc_dir))
        new_files = []
        for fn in file_list:
            file_path = self.path_maker(fn, self.doc_dir)
            if os.path.normpath(file_path) not in existing_sources:
                new_files.append(file_path)
                
        if not new_files:
            print(f"All {len(file_list)} files in '{self.doc_dir}' are already indexed. Skipping.")
            return
            
        print(f"Found {len(new_files)} new file(s) out of {len(file_list)} total. Processing new files...")
        
        # 3. Load and split only the new files
        docs = [PyPDFLoader(fp).load_and_split() for fp in new_files]
        docs_list = [item for sublist in docs for item in sublist]

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size, chunk_overlap=self.chunk_overlap
        )
        doc_splits = text_splitter.split_documents(docs_list)
        
        # 4. Add to vectorDB in batches to respect Google's 100 RPM rate limit
        batch_size = 90 # Safe margin under the 100 limit
        for i in range(0, len(doc_splits), batch_size):
            batch = doc_splits[i:i + batch_size]
            vectordb.add_documents(batch)
            print(f"Processed batch {i // batch_size + 1}/{(len(doc_splits) + batch_size - 1) // batch_size}")
            
            # If there are more batches left, sleep for a minute to reset the quota
            if i + batch_size < len(doc_splits):
                print("Sleeping for 60 seconds to respect free-tier rate limits...")
                time.sleep(60)

        print("VectorDB successfully updated.")
        print("Total number of vectors in vectordb:", vectordb._collection.count(), "\n\n")


if __name__ == "__main__":
    load_dotenv()
    os.environ['GOOGLE_API_KEY'] = os.getenv("GOOGLE_API_KEY")

    with open(here("configs/tools_config.yml")) as cfg:
        app_config = yaml.load(cfg, Loader=yaml.FullLoader)

    rag_configs = ["swiss_airline_policy_rag", "stories_rag"]

    for config_name in rag_configs:
        print(f"Preparing VectorDB for {config_name}...")
        config = app_config[config_name]
        
        prepare_db_instance = PrepareVectorDB(
            doc_dir=config["unstructured_docs"],
            chunk_size=config["chunk_size"],
            chunk_overlap=config["chunk_overlap"],
            embedding_model=config["embedding_model"],
            vectordb_dir=config["vectordb"],
            collection_name=config["collection_name"]
        )

        prepare_db_instance.run()
