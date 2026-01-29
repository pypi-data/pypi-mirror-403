import os
import warnings
import json
import whisper
import pandas as pd
import numpy as np
# from langchain.docstore.document import Document
from langchain_core.documents import Document

# --- DÉPENDANCES ---
try: from sqlalchemy import create_engine
except ImportError: create_engine = None
try: from pymongo import MongoClient
except ImportError: MongoClient = None
try: from neo4j import GraphDatabase
except ImportError: GraphDatabase = None
try: from langchain_community.document_loaders import WebBaseLoader
except ImportError: WebBaseLoader = None
# Gestion YouTube
try: from langchain_community.document_loaders import YoutubeLoader
except ImportError: YoutubeLoader = None

try: from rostaing_ocr import ocr_extractor; HAS_OCR = True
except ImportError: HAS_OCR = False

# IMPORTS LANGCHAIN
from langchain_community.document_loaders import (
    TextLoader, CSVLoader, UnstructuredExcelLoader, 
    UnstructuredPowerPointLoader, UnstructuredWordDocumentLoader, 
    UnstructuredMarkdownLoader, UnstructuredHTMLLoader,
    UnstructuredXMLLoader, UnstructuredEPubLoader
)
from moviepy import VideoFileClip # .editor

warnings.filterwarnings("ignore")

class UniversalLoader:
    def __init__(self):
        print("🎙️  Whisper Initialization...")
        self.whisper_model = whisper.load_model("base")

    # ==========================
    # DEEP PROFILING
    # ==========================
    def _create_summary_doc(self, df, source_name):
        try:
            stats_text = []
            stats_text.append(f"=== STATISTICAL ANALYSIS REPORT: {source_name} ===")
            stats_text.append(f"TYPE: Structured Tabular Data")
            stats_text.append(f"TOTAL NUMBER OF ROWS (RECORDS)): {len(df)}")
            stats_text.append(f"NUMBER OF COLUMNS: {len(df.columns)}")
            stats_text.append(f"LIST OF COLUMNS: {', '.join(df.columns.astype(str))}")
            
            stats_text.append("\n--- COLUMN DETAILS ---")
            
            for col in df.columns:
                if pd.api.types.is_numeric_dtype(df[col]):
                    max_val = df[col].max()
                    min_val = df[col].min()
                    mean_val = df[col].mean()
                    stats_text.append(f"• Column '{col}' (Numeric) : Max={max_val}, Min={min_val}, Average={mean_val:.2f}")
                else:
                    unique_count = df[col].nunique()
                    try:
                        top_vals = df[col].value_counts().head(3).to_dict()
                        stats_text.append(f"• Column '{col}' (Categorical) : {unique_count} unique values. Top: {top_vals}")
                    except:
                        stats_text.append(f"• Column '{col}' (Text)")

            stats_text.append("\n--- TABLE START (First 5 Rows) ---")
            stats_text.append(df.head(5).to_markdown(index=False))
            stats_text.append("\n--- TABLE END (Last 5 Rows) ---")
            stats_text.append(df.tail(5).to_markdown(index=False))
            
            return Document(
                page_content="\n".join(stats_text),
                metadata={"source": source_name, "type": "dataset_deep_stats", "rows": len(df)}
            )
        except Exception as e:
            print(f"⚠️ Profiling Error : {e}")
            return Document(page_content=f"Summary unavailable", metadata={"source": source_name})

    def process_dataframe_object(self, df, source_name="InMemory_DataFrame"):
        try:
            if hasattr(df, "to_pandas"): df = df.to_pandas()
            docs = []
            docs.append(self._create_summary_doc(df, source_name))
            docs.append(Document(page_content=df.to_markdown(index=False), metadata={"source": source_name, "type": "dataframe_content"}))
            return docs
        except Exception as e:
            print(f"❌ DataFrame Error : {e}")
            return []

    # ==========================
    # BASES DE DONNÉES
    # ==========================
    def process_sql(self, config):
        if not create_engine: return []
        uri = config.get("connection_string")
        query = config.get("query", "SELECT * FROM users")
        print(f"🗄️  SQL Query on : {uri.split('@')[-1]}")
        try:
            engine = create_engine(uri)
            with engine.connect() as connection:
                df = pd.read_sql(query, connection)
                return self.process_dataframe_object(df, source_name="sql_query")
        except Exception as e:
            print(f"❌ SQL Error: {e}")
            return []

    # ==========================
    # WEB & YOUTUBE (Version Blindée)
    # ==========================
    def process_web(self, url):
        # 1. Détection YouTube
        if "youtube.com" in url or "youtu.be" in url:
            print(f"🎥 YouTube Video Processing: {url}")
            if not YoutubeLoader:
                print("⚠️ Missing package: 'youtube-transcript-api'.")
                return []
            
            try:
                # ESSAI 1 : Avec métadonnées complètes
                # (Peut échouer si IP bloquée par YouTube)
                loader = YoutubeLoader.from_youtube_url(
                    url, 
                    add_video_info=True, 
                    language=["fr", "en", "fr-FR"]
                )
                docs = loader.load()
            
            except Exception as e:
                # ESSAI 2 : Mode furtif (Juste les sous-titres)
                print(f"⚠️ YouTube Error ({e}). Attempting in simple transcription mode...")
                try:
                    loader = YoutubeLoader.from_youtube_url(
                        url, 
                        add_video_info=False, # Désactive la récupération des infos qui bloque souvent
                        language=["fr", "en"]
                    )
                    docs = loader.load()
                except Exception as fatal_e:
                    print(f"❌ YouTube Fatal Error: {fatal_e}")
                    return []

            # Nettoyage
            for d in docs: d.metadata.update({"type": "youtube_video", "source": url})
            return docs
        
        # 2. Web Classique
        print(f"🌐 Scraping Web : {url}")
        if not WebBaseLoader: return []
        try:
            loader = WebBaseLoader(url)
            docs = loader.load()
            for d in docs: d.metadata.update({"source": url, "type": "web"})
            return docs
        except Exception as e:
            print(f"❌ Web Error: {e}")
            return []

    def process_mongodb(self, config):
        if not MongoClient: return []
        print("🍃 MongoDB Read...")
        try:
            client = MongoClient(config["uri"])
            db = client[config["db"]]
            col = db[config["collection"]]
            limit = config.get("limit", 50)
            count = col.count_documents({}) 
            cursor = col.find().limit(limit)
            text_content = f"MONGODB STATISTICS:\nCollection: {config['collection']}\nTotal Documents: {count}\n\nSAMPLE:\n"
            for doc in cursor:
                doc.pop("_id", None)
                text_content += json.dumps(doc, default=str) + "\n"
            return [Document(page_content=text_content, metadata={"source": "mongodb", "type": "nosql"})]
        except Exception as e:
            print(f"❌ MongoDB Error: {e}")
            return []

    def process_neo4j(self, config):
        if not GraphDatabase: return []
        try:
            driver = GraphDatabase.driver(config["uri"], auth=(config["user"], config["password"]))
            query = config.get("query", "MATCH (n) RETURN n LIMIT 10")
            with driver.session() as session:
                count_res = session.run("MATCH (n) RETURN count(n) as count")
                total = count_res.single()["count"]
                res = session.run(query)
                results = [str(record.data()) for record in res]
            driver.close()
            text_content = f"GRAPH STATISTICS:\nTotal Nodes: {total}\n\nDATA:\n" + "\n".join(results)
            return [Document(page_content=text_content, metadata={"source": "neo4j", "type": "graph"})]
        except Exception as e:
            print(f"❌ Neo4j Error: {e}")
            return []

    # ==========================
    # FICHIERS CLASSIQUES
    # ==========================
    def _process_with_rostaing_ocr(self, file_path):
        if not HAS_OCR: return []
        try:
            print(f"🔍 OCR Layout-Aware : {os.path.basename(file_path)}")
            extractor = ocr_extractor(file_path, print_to_console=False, save_file=False)
            if extractor.status == "Success":
                return [Document(page_content=extractor.extracted_text, metadata={"source": file_path, "type": "ocr"})]
            return []
        except: return []

    def _transcribe_audio(self, p):
        try: return self.whisper_model.transcribe(p)["text"]
        except: return ""

    def _process_video(self, p):
        try:
            base, _ = os.path.splitext(p)
            temp = f"{base}_temp.mp3"
            vid = VideoFileClip(p)
            vid.audio.write_audiofile(temp, verbose=False, logger=None)
            vid.close()
            txt = self._transcribe_audio(temp)
            if os.path.exists(temp): os.remove(temp)
            return txt
        except: return ""

    def load_file(self, file_path):
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext == ".csv":
            try: return self.process_dataframe_object(pd.read_csv(file_path), source_name=os.path.basename(file_path))
            except: pass
        elif ext == ".parquet":
            try: return self.process_dataframe_object(pd.read_parquet(file_path), source_name=os.path.basename(file_path))
            except: pass

        if ext in [".pdf", ".jpg", ".png", ".jpeg", ".bmp", ".tiff", ".webp"]:
            return self._process_with_rostaing_ocr(file_path)

        if ext in [".mp3", ".wav", ".m4a", ".ogg", ".flac", ".webm"]:
            t = self._transcribe_audio(file_path)
            return [Document(page_content=t, metadata={"source": file_path})] if t else []
        if ext in [".mp4", ".avi", ".mov", ".mkv"]:
            t = self._process_video(file_path)
            return [Document(page_content=t, metadata={"source": file_path})] if t else []

        if ext in [".docx", ".doc"]: loader = UnstructuredWordDocumentLoader(file_path)
        elif ext in [".xlsx", ".xls"]: loader = UnstructuredExcelLoader(file_path)
        elif ext in [".pptx", ".ppt"]: loader = UnstructuredPowerPointLoader(file_path)
        
        elif ext in [".html", ".htm"]: loader = UnstructuredHTMLLoader(file_path)
        elif ext == ".xml": loader = UnstructuredXMLLoader(file_path)
        elif ext == ".epub": loader = UnstructuredEPubLoader(file_path)
        elif ext == ".md": loader = UnstructuredMarkdownLoader(file_path)
        elif ext in [".txt", ".json", ".log", ".py", ".js", ".sql", ".yaml", ".ini"]:
            loader = TextLoader(file_path, encoding="utf-8", autodetect_encoding=True)
        else:
            loader = TextLoader(file_path, encoding="utf-8", autodetect_encoding=True)

        try: return loader.load()
        except Exception as e:
            print(f"❌ Load Error {file_path}: {e}")
            return []