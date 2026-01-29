from setuptools import setup, find_packages
import pathlib

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text(encoding="utf-8")

# 1. Dépendances OBLIGATOIRES (Le minimum vital pour que le framework démarre)
core_requirements = [
    "langchain",
    "langchain-community",
    "langchain-core",
    "langchain-text-splitters",
    "fastembed",      # Embeddings par défaut légers
    "chromadb",       # DB par défaut
    "pandas",
    "numpy",
    "watchdog",       # Surveillance fichiers
    "python-dotenv",
    "pyttsx3",        # Vocal basique
]

# 2. Dépendances OPTIONNELLES (À la carte)
extra_requirements = {
    # Pour utiliser les LLMs distants
    "llms": [
        "langchain-ollama",
        "langchain-openai",
        "langchain-anthropic",
        "langchain-google-genai",
        "langchain-groq",
        "langchain-mistralai",
        "langchain-huggingface",
        "huggingface-hub",
    ],
    # Pour les bases de données (SQL, NoSQL, Graph)
    "database": [
        "sqlalchemy",
        "pymongo",
        "neo4j",
        "psycopg2-binary", # Postgres
        "pymssql",         # SQL Server
        "pymysql",         # MySQL
        "psycopg",
        # "cx-oracle"      # Souvent complexe à installer (nécessite drivers OS), on le laisse dans 'all'
    ],
    # Pour les autres Vector Stores
    "vectors": [
        "faiss-cpu",
        "qdrant-client",
        "langchain-chroma"
    ],
    # Pour le Multimédia (YouTube, Audio, Vidéo, Web)
    "media": [
        "openai-whisper",
        "moviepy",
        "soundfile",
        "youtube-transcript-api",
        "pytube",
        "beautifulsoup4",
        "html2text",
    ],
    # Pour les documents bureautiques et l'OCR avancé
    "docs": [
        "rostaing-ocr",
        "python-docx",
        "openpyxl",
        "python-pptx",
        "unstructured",
    ],
    # Outils avancés HuggingFace
    "hf": [
        "hf-xet",
        "hf-transfer",
        "sentence-transformers"
    ]
}

# Création d'une option "all" pour tout installer d'un coup
# Cela combine toutes les listes ci-dessus + cx-oracle
all_reqs = sum(extra_requirements.values(), []) + ["cx-oracle"]
extra_requirements["all"] = all_reqs

setup(
    name="rostaingchain",
    version="0.2.3",
    description="The Ultimate Hybrid RAG Framework: Local/Remote LLMs, Live Watcher, Deep Profiling & Security.",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/Rostaing/rostaingchain",
    author="Davila Rostaing",
    author_email="rostaingdavila@gmail.com",
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    packages=find_packages(),
    include_package_data=True,
    
    # Installation légère par défaut
    install_requires=core_requirements,
    
    # Installation complète ou modulaire
    extras_require=extra_requirements,
    
    # Point d'entrée CLI (Optionnel, décommentez si vous avez une fonction main dans core.py)
    # entry_points={
    #     "console_scripts": [
    #         "rostaingchain=rostaingchain.core:main",
    #     ]
    # },
)