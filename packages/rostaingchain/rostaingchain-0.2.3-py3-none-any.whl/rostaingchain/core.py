import os
import threading
import pandas as pd
# from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_text_splitters import RecursiveCharacterTextSplitter
# from langchain.docstore.document import Document
from langchain_core.documents import Document

# Imports internes
from .llm_engine import LLMEngine
from .vector_store import VectorDBFactory
from .loaders import UniversalLoader
from .watcher import RostaingWatcher, PollingWatcher
from .embeddings import EmbeddingsManager

class RostaingBrain:
    def __init__(self, 
                 llm_model="llama3.2", 
                 llm_provider="auto",
                 llm_api_key=None,
                 llm_base_url=None,
                 embedding_model="BAAI/bge-small-en-v1.5",
                 embedding_source="fastembed",
                 vector_db="chroma",   
                 data_source="./data", 
                 auto_update=True,
                 poll_interval=60,
                 reset_db=False,
                 memory=False,
                 # --- PARAMÈTRES LLM ---
                 temperature=0.1,
                 max_tokens=None,
                 top_p=None,
                 top_k=None,
                 cache=True,
                 # --- SÉCURITÉ (NOUVEAU) ---
                 security_filters=None): # Liste ["BIC", "EMAIL"] ou True/False
        
        self.db_type = vector_db
        self.memory_object = None
        self.db_config = None
        self.web_url = None
        
        self.use_memory = memory
        self.chat_history = [] 
        
        # --- DÉTECTION SOURCE ---
        if isinstance(data_source, dict):
            self.mode = "database"; self.db_config = data_source; self.watch_target = None
            print(f"🗄️  DATABASE MODE: {data_source.get('type', 'sql').upper()}")
        elif isinstance(data_source, str):
            if data_source.startswith("http"): self.mode = "web"; self.web_url = data_source; print(f"🌐 WEB MODE")
            else:
                self.abs_path = os.path.abspath(data_source)
                if os.path.splitext(self.abs_path)[1]: self.mode = "file"; self.watch_target = os.path.dirname(self.abs_path) or os.getcwd(); self.target_filename = os.path.basename(self.abs_path); print(f"📄 SINGLE FILE MODE")
                else: self.mode = "directory"; self.watch_target = self.abs_path; print(f"📁 FOLDER MODE")
        else:
            self.mode = "memory"; self.memory_object = data_source; print(f"📊 MEMORY MODE"); auto_update = False 

        print(f"🧠 Init RostaingBrain ({llm_model})")

        if reset_db: VectorDBFactory.reset("./db_storage")

        self.embed_manager = EmbeddingsManager(model_name=embedding_model, source=embedding_source)
        self.embedding_function = self.embed_manager.get_function()
        self.loader = UniversalLoader()
        self.db = VectorDBFactory.create(vector_db, self.embedding_function)
        
        # Transmission des params
        llm_kwargs = {}
        if max_tokens: llm_kwargs['max_tokens'] = max_tokens
        if top_p: llm_kwargs['top_p'] = top_p
        if top_k: llm_kwargs['top_k'] = top_k
        
        self.engine = LLMEngine(
            model_name=llm_model, 
            provider=llm_provider, 
            api_key=llm_api_key, 
            base_url=llm_base_url,
            temperature=temperature,
            use_cache=cache,
            security_filters=security_filters, # <--- Passage des filtres
            **llm_kwargs
        )
        
        self._initial_ingest()
        
        if auto_update and self.mode != "memory":
            if self.mode in ["database", "web"]:
                self.watcher = PollingWatcher(self._on_polling_event, data_source if self.mode == "database" else self.web_url, interval=poll_interval)
                self.watcher.start()
            elif self.mode in ["directory", "file"]:
                if self.mode == "directory" and not os.path.exists(self.watch_target): os.makedirs(self.watch_target)
                self.watcher = RostaingWatcher(self._on_file_event, self.watch_target)
                t = threading.Thread(target=self.watcher.start); t.daemon = True; t.start()
                print(f"👁️  Active monitoring.")

    # ... (Le reste des méthodes reste identique) ...
    # Je copie ici les méthodes indispensables pour que le code soit complet
    def _initial_ingest(self):
        if self.mode == "database": self._process_database(self.db_config)
        elif self.mode == "web": self._process_web(self.web_url)
        elif self.mode == "memory": self._ingest_memory_object()
        else: self._ingest_existing_files()

    def _process_database(self, c): docs=self.loader.process_sql(c) if c.get("type","sql")=="sql" else (self.loader.process_mongodb(c) if c.get("type")=="mongodb" else self.loader.process_neo4j(c)); self._update_db(docs)
    def _process_web(self, u): docs=self.loader.process_web(u); self._update_db(docs)
    def _ingest_memory_object(self): docs=self.loader.process_dataframe_object(self.memory_object); self._update_db(docs)

    def _update_db(self, docs):
        if not docs: return
        splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=300)
        chunks = splitter.split_documents(docs)
        self.db = VectorDBFactory.add_docs(self.db, chunks, self.db_type, self.embedding_function, "./db_storage")
        print(f"✅ RAG updated ({len(chunks)} chunks).")

    def _on_polling_event(self, c): 
        if self.mode=="database": self._process_database(c)
        else: self._process_web(c)
    def _on_file_event(self, p):
        p=os.path.abspath(p)
        if self.mode=="file": 
            if p==self.abs_path: self.process_file(p)
        else: self.process_file(p)
    def process_file(self, file_path):
        if not os.path.exists(file_path) or "~" in file_path: return
        try: 
            print(f"⚙️ {os.path.basename(file_path)}")
            self._update_db(self.loader.load_file(file_path))
        except: pass
    def _ingest_existing_files(self):
        if self.mode=="file": 
            if os.path.exists(self.abs_path): self.process_file(self.abs_path)
        else:
            if not os.path.exists(self.watch_target): os.makedirs(self.watch_target); return
            for r,_,fs in os.walk(self.watch_target): 
                for f in fs: self.process_file(os.path.join(r,f))

    def _safe_retrieval(self, query):
        docs = []
        try:
            if self.db: 
                retriever = self.db.as_retriever(search_type="mmr", search_kwargs={"k": 6, "fetch_k": 20})
                docs = retriever.invoke(query)
        except Exception as e: print(f"⚠️ Retrieval Error: {e}")
        return docs

    def chat(self, user_query, image_path=None, vocal_response=False, stream=False, output_format="text"):
        docs = self._safe_retrieval(user_query)
        context = "\n\n".join([d.page_content for d in docs]) if docs else ""
        if context: print(f"📘 Context used : {len(docs)} segments.")
        else: print("⚠️  No RAG context found.")
        
        if self.use_memory and self.chat_history:
            history = "HISTORY:\n" + "\n".join([f"User:{q}\nAI:{a}" for q,a in self.chat_history[-5:]])
            context = f"{history}\n\nRAG CONTEXT:\n{context}"

        response = self.engine.generate(user_query, context=context, image_path=image_path, vocal_out=vocal_response, stream=stream, output_format=output_format)
        if self.use_memory and not stream: self.chat_history.append((user_query, response))
        return response