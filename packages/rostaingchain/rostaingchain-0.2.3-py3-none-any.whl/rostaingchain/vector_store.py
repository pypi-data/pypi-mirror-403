import os
import shutil
import hashlib

# Imports LangChain pour les bases locales
from langchain_chroma import Chroma
from langchain_community.vectorstores import FAISS, Qdrant

# Import Client Qdrant
try:
    from qdrant_client import QdrantClient
    from qdrant_client.http import models as qdrant_models
except ImportError:
    QdrantClient = None

class VectorDBFactory:
    @staticmethod
    def reset(persist_directory="./db_storage"):
        """Physical cleanup of the storage folder."""
        if os.path.exists(persist_directory):
            try:
                def on_rm_error(func, path, exc_info):
                    try:
                        os.chmod(path, 0o777)
                        os.remove(path)
                    except: pass
                shutil.rmtree(persist_directory, onerror=on_rm_error)
                print(f"🧹 DB folder deleted: {persist_directory}")
            except Exception as e:
                print(f"⚠️ DB cleanup error: {e}")

    @staticmethod
    def create(db_type, embedding_function, persist_directory="./db_storage"):
        """Load an existing DB."""
        db_type = db_type.lower()
        
        if db_type == "chroma":
            return Chroma(persist_directory=persist_directory, embedding_function=embedding_function)
        
        elif db_type == "faiss":
            try:
                return FAISS.load_local(persist_directory, embedding_function, allow_dangerous_deserialization=True)
            except: return None 

        elif db_type == "qdrant":
            if os.path.exists(persist_directory):
                try:
                    client = QdrantClient(path=persist_directory)
                    cols = client.get_collections().collections
                    if any(c.name == "rostaing_collection" for c in cols):
                        return Qdrant(
                            client=client, 
                            collection_name="rostaing_collection", 
                            embeddings=embedding_function,
                            content_payload_key="page_content",
                            metadata_payload_key="metadata"
                        )
                except: return None
            return None

        else:
            raise ValueError(f"Database '{db_type}' not supported.")

    @staticmethod
    def _generate_ids(docs):
        """Generate unique IDs based on content to avoid duplicates."""
        ids = []
        for doc in docs:
            # Hash du contenu + source pour l'unicité
            content_str = f"{doc.page_content}-{doc.metadata.get('source', '')}"
            hash_id = hashlib.md5(content_str.encode('utf-8')).hexdigest()
            ids.append(hash_id)
        return ids

    @staticmethod
    def add_docs(db_instance, docs, db_type, embedding_function, persist_directory="./db_storage"):
        """Add documents with deduplication (IDs)."""
        if not docs: return db_instance
        db_type = db_type.lower()
        
        # Génération des IDs uniques pour éviter la duplication si reset_db=False
        ids = VectorDBFactory._generate_ids(docs)

        # --- CAS 1 : CRÉATION INITIALE ---
        if db_instance is None:
            print(f"✨ Initial database creation {db_type.upper()}...")
            
            if db_type == "faiss":
                # FAISS ne gère pas nativement les IDs aussi facilement pour la dédup, 
                # mais on initialise propre.
                db = FAISS.from_documents(docs, embedding_function)
                db.save_local(persist_directory)
                return db

            elif db_type == "qdrant":
                if not QdrantClient: raise ImportError("pip install qdrant-client")
                
                dummy_vec = embedding_function.embed_query("test")
                vector_size = len(dummy_vec)
                
                client = QdrantClient(path=persist_directory)
                client.recreate_collection(
                    collection_name="rostaing_collection",
                    vectors_config=qdrant_models.VectorParams(
                        size=vector_size, 
                        distance=qdrant_models.Distance.COSINE
                    )
                )
                
                db = Qdrant(
                    client=client, 
                    collection_name="rostaing_collection", 
                    embeddings=embedding_function,
                    content_payload_key="page_content",
                    metadata_payload_key="metadata"
                )
                # Ajout avec IDs
                db.add_documents(docs, ids=ids)
                return db
            
            elif db_type == "chroma":
                # Chroma gère très bien les IDs pour l'upsert (mise à jour si existe)
                return Chroma.from_documents(
                    docs, 
                    embedding_function, 
                    persist_directory=persist_directory,
                    ids=ids
                )

        # --- CAS 2 : MISE À JOUR ---
        else:
            try:
                # L'ajout avec IDs permet à Chroma/Qdrant d'ignorer ou mettre à jour les doublons
                # au lieu de les ajouter bêtement.
                if db_type == "faiss":
                    # Pour FAISS, on ajoute tout (la dédup est plus complexe sur fichier plat)
                    db_instance.add_documents(docs)
                    db_instance.save_local(persist_directory)
                else:
                    db_instance.add_documents(docs, ids=ids)
                    
                return db_instance
            except Exception as e:
                print(f"❌ Error while adding to the DB: {e}")
                return db_instance