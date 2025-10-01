"""
Centralized configuration management for the Rule-Anchored Localization QA System
"""

import os
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Centralized configuration class following OOP principles"""
    
    def __init__(self):
        # LM Studio Configuration
        self.CHAT_BASE_URL = os.getenv("CHAT_BASE_URL", "http://localhost:1234/v1")
        self.EMBED_BASE_URL = os.getenv("EMBED_BASE_URL", "http://127.0.0.1:1234/v1")
        self.CHAT_MODEL = os.getenv("CHAT_MODEL", "qwen/qwen3-1.7b")
        self.EMBED_MODEL = os.getenv("EMBED_MODEL", "text-embedding-nomic-embed-text-v1.5")
        
        # Scoring Configuration
        self.SEVERITY_MULTIPLIER_MINOR = int(os.getenv("SEVERITY_MULTIPLIER_MINOR", "1"))
        self.SEVERITY_MULTIPLIER_MAJOR = int(os.getenv("SEVERITY_MULTIPLIER_MAJOR", "2"))
        self.SEVERITY_MULTIPLIER_CRITICAL = int(os.getenv("SEVERITY_MULTIPLIER_CRITICAL", "3"))
        self.STYLE_PUNCTUATION_CAP = int(os.getenv("STYLE_PUNCTUATION_CAP", "30"))
        
        # Default Weights by Macro Class
        self.WEIGHT_ACCURACY = int(os.getenv("WEIGHT_ACCURACY", "5"))
        self.WEIGHT_TERMINOLOGY = int(os.getenv("WEIGHT_TERMINOLOGY", "4"))
        self.WEIGHT_MECHANICS = int(os.getenv("WEIGHT_MECHANICS", "3"))
        self.WEIGHT_PUNCTUATION = int(os.getenv("WEIGHT_PUNCTUATION", "2"))
        self.WEIGHT_STYLE = int(os.getenv("WEIGHT_STYLE", "1"))
        self.WEIGHT_LEGAL = int(os.getenv("WEIGHT_LEGAL", "6"))
        self.WEIGHT_STANDARDS = int(os.getenv("WEIGHT_STANDARDS", "3"))
        
        # Application Settings
        self.DEBUG = os.getenv("DEBUG", "false").lower() == "true"
        self.DATA_DIR = os.getenv("DATA_DIR", "./data")
        self.UPLOAD_MAX_SIZE = int(os.getenv("UPLOAD_MAX_SIZE", "10485760"))  # 10MB
        
        # Model Prompt Versions
        self.MODEL_PROMPT_VERSION = os.getenv("MODEL_PROMPT_VERSION", "1.0.0")
    
    def get_severity_multipliers(self) -> Dict[str, int]:
        """Get severity multipliers as a dictionary"""
        return {
            "Minor": self.SEVERITY_MULTIPLIER_MINOR,
            "Major": self.SEVERITY_MULTIPLIER_MAJOR,
            "Critical": self.SEVERITY_MULTIPLIER_CRITICAL
        }
    
    def get_default_weights(self) -> Dict[str, int]:
        """Get default weights by macro class"""
        return {
            "Accuracy": self.WEIGHT_ACCURACY,
            "Terminology": self.WEIGHT_TERMINOLOGY,
            "Mechanics": self.WEIGHT_MECHANICS,
            "Punctuation": self.WEIGHT_PUNCTUATION,
            "Style": self.WEIGHT_STYLE,
            "Legal": self.WEIGHT_LEGAL,
            "Standards": self.WEIGHT_STANDARDS
        }
    
    def get_lm_studio_config(self) -> Dict[str, str]:
        """Get LM Studio configuration"""
        return {
            "chat_base_url": self.CHAT_BASE_URL,
            "embed_base_url": self.EMBED_BASE_URL,
            "chat_model": self.CHAT_MODEL,
            "embed_model": self.EMBED_MODEL
        }
    
    def validate(self) -> bool:
        """Validate configuration and check LM Studio connectivity"""
        issues = []
        
        # Check required environment variables
        if not self.CHAT_MODEL:
            issues.append("CHAT_MODEL not configured")
        if not self.EMBED_MODEL:
            issues.append("EMBED_MODEL not configured")
        if not self.CHAT_BASE_URL:
            issues.append("CHAT_BASE_URL not configured")
        if not self.EMBED_BASE_URL:
            issues.append("EMBED_BASE_URL not configured")
        
        # Check data directory
        if not os.path.exists(self.DATA_DIR):
            print(f"⚠️  Data directory {self.DATA_DIR} does not exist, creating...")
            os.makedirs(self.DATA_DIR, exist_ok=True)
            os.makedirs(os.path.join(self.DATA_DIR, "uploads"), exist_ok=True)
            os.makedirs(os.path.join(self.DATA_DIR, "knowledge_bases"), exist_ok=True)
            os.makedirs(os.path.join(self.DATA_DIR, "evaluations"), exist_ok=True)
            os.makedirs(os.path.join(self.DATA_DIR, "embeddings"), exist_ok=True)
            os.makedirs(os.path.join(self.DATA_DIR, "feedback"), exist_ok=True)
        
        if issues:
            print("❌ Configuration validation failed:")
            for issue in issues:
                print(f"   - {issue}")
            return False
        
        print("✅ Configuration validated successfully")
        return True
    
    def __repr__(self) -> str:
        """String representation for debugging"""
        return f"Config(chat_model={self.CHAT_MODEL}, embed_model={self.EMBED_MODEL})"

# Global configuration instance
config = Config()

# Validate on import
if __name__ != "__main__":
    config.validate()
