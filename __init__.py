"""
AI Article Generator - Main Package
A comprehensive article generation system with AI-powered content creation,
SEO optimization, and professional export capabilities.
"""

__version__ = "1.0.0"
__author__ = "AI Article Generator"
__description__ = "Professional AI-powered content creation with stunning visuals"

# Package metadata
PACKAGE_NAME = "ai-article-generator"
PACKAGE_URL = "https://github.com/your-username/ai-article-generator"

# Default configuration
DEFAULT_CONFIG = {
    "max_tokens": 4000,
    "temperature": 0.7,
    "default_language": "English",
    "default_tone": "Professional",
    "default_sections": 5,
    "default_word_count": 600,
    "image_size": "1024x1024",
    "max_images": 5
}

# Supported languages
SUPPORTED_LANGUAGES = [
    "English", "Spanish", "French", "German", 
    "Italian", "Portuguese", "Dutch"
]

# Available tones
AVAILABLE_TONES = [
    "Professional", "Conversational", "Academic", 
    "Elegant", "Warm", "Technical", "Creative"
]

# Export formats
EXPORT_FORMATS = ["HTML", "DOCX", "JSON"]