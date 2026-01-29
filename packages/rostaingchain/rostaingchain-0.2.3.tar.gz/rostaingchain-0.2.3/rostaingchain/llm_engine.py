import os
import pyttsx3
from langchain_core.messages import HumanMessage
# from langchain.globals import set_llm_cache
from langchain_core.globals import set_llm_cache
from langchain_community.cache import InMemoryCache
from .security import SecurityManager

# Imports conditionnels
try: from langchain_ollama import ChatOllama
except ImportError: ChatOllama = None
try: from langchain_openai import ChatOpenAI
except ImportError: ChatOpenAI = None
try: from langchain_anthropic import ChatAnthropic
except ImportError: ChatAnthropic = None
try: from langchain_google_genai import ChatGoogleGenerativeAI
except ImportError: ChatGoogleGenerativeAI = None
try: from langchain_groq import ChatGroq
except ImportError: ChatGroq = None
try: from langchain_mistralai import ChatMistralAI
except ImportError: ChatMistralAI = None

class LLMEngine:
    def __init__(self, 
                 model_name="llama3.2", 
                 provider="auto", 
                 api_key=None, 
                 base_url=None, 
                 temperature=0.1,
                 use_cache=False,
                 security_filters=None, # <--- Remplace security_active (peut être True ou liste)
                 **llm_kwargs):
        
        self.model_name = model_name
        self.provider = provider.lower()
        self.temperature = temperature
        self.api_key = api_key
        self.base_url = base_url
        self.llm_kwargs = llm_kwargs
        
        # Init Sécurité avec les filtres spécifiques
        self.security = SecurityManager(filters=security_filters)
        
        # Init Cache
        if use_cache:
            set_llm_cache(InMemoryCache())
            print("🚀 LLM cache enabled.")
        else:
            set_llm_cache(None)

        try:
            self.tts_engine = pyttsx3.init()
            self.tts_engine.setProperty('rate', 170)
        except: self.tts_engine = None

        if self.provider == "auto":
            self.provider = self._detect_provider(model_name)
        
        print(f"🤖 Engine enabled: {self.provider.upper()} ({self.model_name}) | Security: {list(self.security.active_patterns.keys()) if self.security.is_active else 'OFF'}")
        self.llm = self._create_llm_instance()

    def _detect_provider(self, name):
        name = name.lower()
        if "gpt" in name or "o1-" in name: return "openai"
        if "claude" in name: return "anthropic"
        if "gemini" in name: return "google"
        if "mixtral" in name or "llama3-70b" in name: return "groq"
        if "mistral" in name: return "mistral"
        if "deepseek" in name: return "deepseek"
        if "grok" in name: return "grok"
        return "ollama"

    def _create_llm_instance(self):
        if self.provider == "ollama":
            if not ChatOllama: raise ImportError("pip install langchain-ollama")
            return ChatOllama(model=self.model_name, temperature=self.temperature, base_url=self.base_url or "http://localhost:11434", **self.llm_kwargs)
        elif self.provider == "openai":
            if not ChatOpenAI: raise ImportError("pip install langchain-openai")
            return ChatOpenAI(model=self.model_name, api_key=self.api_key or os.getenv("OPENAI_API_KEY"), temperature=self.temperature, **self.llm_kwargs)
        elif self.provider == "anthropic":
            if not ChatAnthropic: raise ImportError("pip install langchain-anthropic")
            return ChatAnthropic(model_name=self.model_name, api_key=self.api_key or os.getenv("ANTHROPIC_API_KEY"), temperature=self.temperature, **self.llm_kwargs)
        elif self.provider == "google":
            if not ChatGoogleGenerativeAI: raise ImportError("pip install langchain-google-genai")
            return ChatGoogleGenerativeAI(model=self.model_name, google_api_key=self.api_key or os.getenv("GOOGLE_API_KEY"), temperature=self.temperature, **self.llm_kwargs)
        elif self.provider == "groq":
            if not ChatGroq: raise ImportError("pip install langchain-groq")
            return ChatGroq(model_name=self.model_name, api_key=self.api_key or os.getenv("GROQ_API_KEY"), temperature=self.temperature, **self.llm_kwargs)
        elif self.provider == "mistral":
            if not ChatMistralAI: raise ImportError("pip install langchain-mistralai")
            return ChatMistralAI(model=self.model_name, api_key=self.api_key or os.getenv("MISTRAL_API_KEY"), temperature=self.temperature, **self.llm_kwargs)
        elif self.provider in ["deepseek", "grok", "custom", "xai"]:
            if not ChatOpenAI: raise ImportError("pip install langchain-openai")
            url = self.base_url
            key = self.api_key
            if self.provider == "deepseek" and not url: url, key = "https://api.deepseek.com/v1", key or os.getenv("DEEPSEEK_API_KEY")
            elif self.provider == "grok" and not url: url, key = "https://api.x.ai/v1", key or os.getenv("XAI_API_KEY")
            return ChatOpenAI(model=self.model_name, api_key=key, base_url=url, temperature=self.temperature, **self.llm_kwargs)
        else: raise ValueError(f"Provider inconnu : {self.provider}")

    def generate(self, prompt, context=None, image_path=None, vocal_out=False, stream=False, output_format="text"):
        messages = []
        
        format_instruction = ""
        if output_format == "json": format_instruction = "\nIMPORTANT: Respond only in valid JSON."
        elif output_format == "markdown": format_instruction = "\nIMPORTANT: Use Markdown format."
        elif output_format == "toon": format_instruction = "\nSTYLE: You are a cartoon character!"
        
        # Instruction système de sécurité dynamique
        if self.security.is_active:
            filters_list = ", ".join(self.security.active_patterns.keys())
            format_instruction += f"\nSECURITY: The following data is CONFIDENTIAL: [{filters_list}]. Never display them. Replace them with a note indicating they are protected."

        final_prompt = prompt + format_instruction
        if context:
            final_prompt = (
                "You are an expert assistant. Use the context below.\n"
                f"--- CONTEXT ---\n{context}\n----------------\n"
                f"QUESTION: {final_prompt}"
            )
            
        content = [{"type": "text", "text": final_prompt}]

        if image_path:
            import base64
            try:
                with open(image_path, "rb") as f:
                    enc = base64.b64encode(f.read()).decode("utf-8")
                content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{enc}"}})
            except: pass
            
        messages.append(HumanMessage(content=content))
        
        if stream:
            return self._stream_response_generator(messages, vocal_out)
        else:
            try:
                response_obj = self.llm.invoke(messages)
                clean_text = self.security.scrub(response_obj.content)
                if vocal_out and self.tts_engine: self.speak(clean_text)
                return clean_text
            except Exception as e:
                return f"❌ Erreur : {e}"

    def _stream_response_generator(self, messages, vocal_out):
        """Generator with BUFFER to secure streaming."""
        full_text_buffer = ""
        display_buffer = ""
        
        try:
            for chunk in self.llm.stream(messages):
                token = chunk.content
                if token:
                    display_buffer += token
                    
                    # On affiche quand on a assez de contexte pour que les regex fonctionnent
                    if len(display_buffer) > 25 or token in [".", "\n", "!", "?", " "]:
                        clean_chunk = self.security.scrub(display_buffer)
                        yield clean_chunk
                        full_text_buffer += clean_chunk
                        display_buffer = ""
            
            # Fin du buffer
            if display_buffer:
                clean_chunk = self.security.scrub(display_buffer)
                full_text_buffer += clean_chunk
                yield clean_chunk

            if vocal_out and self.tts_engine: self.speak(full_text_buffer)
            
        except Exception as e:
            yield f"❌ Stream Error: {e}"

    def speak(self, text):
        try:
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()
        except: pass