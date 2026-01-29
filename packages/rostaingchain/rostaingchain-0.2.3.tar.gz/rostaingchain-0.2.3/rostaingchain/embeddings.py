import os
import shutil
from langchain_community.embeddings import FastEmbedEmbeddings
from langchain_ollama import OllamaEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings

class EmbeddingsManager:
    def __init__(self, 
                 model_name="BAAI/bge-small-en-v1.5", 
                 source="fastembed", 
                 device="cpu", 
                 api_key=None):
        
        self.source = source.lower()
        self.model_name = model_name
        self.device = device
        self.api_key = api_key
        
        # Désactivation explicite de hf_transfer sur Windows pour éviter la corruption de fichiers
        # Le téléchargeur standard est plus lent mais beaucoup plus fiable.
        os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "0"
        
        self.model = self._load_model()

    def _load_model(self):
        print(f"🔌 Loading embeddings : {self.source} ({self.model_name})...")
        
        if self.source == "fastembed":
            cache_path = os.path.abspath("./embedding_cache")
            if not os.path.exists(cache_path):
                os.makedirs(cache_path)

            try:
                return FastEmbedEmbeddings(
                    model_name=self.model_name,
                    threads=None, 
                    cache_dir=cache_path,
                )
            except Exception as e:
                # Gestion automatique du cache corrompu
                if "NO_SUCHFILE" in str(e) or "File doesn't exist" in str(e):
                    print("⚠️ Corrupted cache detected. Attempting repair...")
                    # On supprime le cache et on réessaie une fois
                    if os.path.exists(cache_path):
                        shutil.rmtree(cache_path)
                        os.makedirs(cache_path)
                    
                    print("🔄 Re-downloading the model (Standard mode)...")
                    return FastEmbedEmbeddings(
                        model_name=self.model_name,
                        threads=None, 
                        cache_dir=cache_path,
                    )
                else:
                    raise e
        
        elif self.source == "ollama":
            return OllamaEmbeddings(
                model=self.model_name,
                base_url="http://localhost:11434"
            )
        
        elif self.source == "huggingface":
            return HuggingFaceEmbeddings(
                model_name=self.model_name,
                model_kwargs={'device': self.device},
                encode_kwargs={'normalize_embeddings': True}
            )

        elif self.source == "openai":
            try:
                from langchain_openai import OpenAIEmbeddings
                return OpenAIEmbeddings(
                    model=self.model_name or "text-embedding-3-small",
                    api_key=self.api_key or os.getenv("OPENAI_API_KEY")
                )
            except ImportError:
                raise ImportError("Install: pip install langchain-openai")
        
        else:
            raise ValueError(f"Unknown source: {self.source}")

    def get_function(self):
        return self.model