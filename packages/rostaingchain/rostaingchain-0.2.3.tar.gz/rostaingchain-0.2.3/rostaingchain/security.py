import re

class SecurityManager:
    def __init__(self, filters=None):
        """
        DLP Security Manager (Data Loss Prevention).
        """
        # Définition de la bibliothèque de patterns
        self.library = {
             # --- IDENTITÉ & CONTACT ---
            "EMAIL": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            "PHONE": r'\b(?:\+|00|0)(?:[\s.\-\(\)]*\d){7,15}\b',
            "ID_NUM": r'\b\d{13,15}\b|\b\d{9}\b|\b\d{14}\b', # SIRET, SIREN, Sécu FR
            "PASSPORT": r'\b[A-Z]{1,2}[0-9]{6,9}\b', # NOUVEAU : Passeports
            "SSN": r'\b\d{3}-\d{2}-\d{4}\b', # NOUVEAU : Secu US (souvent utilisé en data test)

            # --- LOCALISATION (NOUVEAU) ---
            # Détecte : 10 rue de la Paix, 45 Avenue Foch, 123 Main Street...
            # (?i) rend le regex insensible à la casse
            # "ADDRESS": r'(?i)\b\d{1,5}[,\s]+(?:bis|ter|quat)?\s*(?:rue|avenue|av\.?|boulevard|bd|place|pl\.?|impasse|allée|quai|route|chemin|lane|street|road|drive|way|sq\.?|square)\s+[\w\s\-\']+',
            
            # Détecte : BP 1234, 75000 Paris, 10001 New York...
            # (Code postal 5 chiffres + Ville) OU (Boite Postale)
            "POSTAL": r'(?i)(?:\b(?:BP|P\.O\.?\s*Box|CS|TSA)\s*\d+\b)|(?:\b\d{5}|\b\d{4}|\b[A-Z0-9]{3,7})\s+[A-Z][a-zA-Z\s\-]+',

            # --- FINANCES ---
            "BIC": r'\b[A-Z]{4}[A-Z]{2}[A-Z0-9]{2}([A-Z0-9]{3})?\b',
            "IBAN": r'\b[A-Z]{2}\d{2}[A-Z0-9]{4}\d{7}([A-Z0-9]?){0,16}\b',
            "VAT_ID": r'\b[A-Z]{2}\s*[0-9A-Z\.\-]{8,15}\b',
            "CREDIT_CARD": r'\b(?:\d[ -]*?){13,19}\b',
            "MONEY": r'\b\d{1,3}(?:[\s.,]\d{3})*(?:[\.,]\d+)?\s?(?:€|\$|£|EUR|USD|XAF|FCFA)\b',
            "CRYPTO": r'\b(0x[a-fA-F0-9]{40}|[13][a-km-zA-H-J-NP-Z1-9]{25,34})\b', # NOUVEAU : Bitcoin/Ethereum

            # --- TECHNIQUE / IT (Critique pour entreprise) ---
            "IP_ADDR": r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',
            "MAC_ADDR": r'\b([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})\b', # NOUVEAU : Adresse MAC
            # NOUVEAU : Clés API (AWS, Stripe, GitHub, et chaînes longues aléatoires)
            "API_KEY": r'\b((?:AKIA|ABIA|ACCA|ASIA)[0-9A-Z]{16})|(sk_live_[0-9a-zA-Z]{24,})|(ghp_[0-9a-zA-Z]{36})|([a-zA-Z0-9]{32,})\b',
            
            # --- DIVERS ---
            "DATE": r'\b\d{2}[/-]\d{2}[/-]\d{4}\b|\b\d{4}[/-]\d{2}[/-]\d{2}\b', 
        }

        # --- NOUVEAU : Messages compréhensibles pour l'utilisateur ---
        self.friendly_messages = {
            "EMAIL": "[Email masked for confidentiality]",
            "PHONE": "[Phone number masked]",
            "ID_NUM": "[Company/Personal ID masked]",
            "PASSPORT": "[Passport number masked]",
            "SSN": "[Social Security Number masked]",

             # Messages Localisation
            # "ADDRESS": "[Physical address masked for security]",
            "POSTAL": "[City/Postal Code masked]",
            
            "BIC": "[BIC code confidential]",
            "IBAN": "[IBAN bank details protected]",
            "VAT_ID": "[Intracommunity VAT number masked]",
            "CREDIT_CARD": "[Credit card number masked]",
            "MONEY": "[Financial amount masked]",
            "CRYPTO": "[Crypto wallet address masked]",
            
            "IP_ADDR": "[IP address masked]",
            "MAC_ADDR": "[MAC address masked]",
            "API_KEY": "[API Key/Secret redacted for security]",
            
            "DATE": "[Date masked]"
        }

        self.active_patterns = {}

        # Logique d'activation
        if filters is True:
            self.active_patterns = self.library
        elif isinstance(filters, list):
            for key in filters:
                key_upper = key.upper()
                if key_upper in self.library:
                    self.active_patterns[key_upper] = self.library[key_upper]
                else:
                    print(f"⚠️ Unknown security filter ignored: {key}")
        
        self.is_active = len(self.active_patterns) > 0

    def scrub(self, text):
        """
        Clean the text by replacing the data with clear messages.
        """
        if not self.is_active or not text:
            return text

        # 1. Censure par Patterns Regex
        for label, regex in self.active_patterns.items():
            # On récupère le message "friendly", sinon un message par défaut
            replacement_msg = self.friendly_messages.get(label, "[Sensitive data masked]")
            # On remplace la donnée trouvée par le message clair
            text = re.sub(regex, replacement_msg, text)

        return text