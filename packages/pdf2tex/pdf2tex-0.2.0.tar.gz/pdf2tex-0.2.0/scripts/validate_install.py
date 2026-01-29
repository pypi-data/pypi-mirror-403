#!/usr/bin/env python3
"""
Script to validate a PDF2TeX installation and configuration.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def check_python_version() -> bool:
    """Check Python version."""
    print("Checking Python version...", end=" ")
    if sys.version_info >= (3, 11):
        print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor}")
        return True
    else:
        print(f"✗ Python {sys.version_info.major}.{sys.version_info.minor} (requires 3.11+)")
        return False


def check_dependencies() -> bool:
    """Check required dependencies."""
    print("\nChecking dependencies:")
    all_ok = True
    
    dependencies = [
        ("pydantic", "Pydantic"),
        ("pydantic_settings", "Pydantic Settings"),
        ("fastapi", "FastAPI"),
        ("uvicorn", "Uvicorn"),
        ("typer", "Typer"),
        ("rich", "Rich"),
        ("fitz", "PyMuPDF"),
        ("torch", "PyTorch"),
        ("transformers", "Transformers"),
        ("sentence_transformers", "Sentence Transformers"),
        ("qdrant_client", "Qdrant Client"),
    ]
    
    for module, name in dependencies:
        print(f"  {name}...", end=" ")
        try:
            __import__(module)
            print("✓")
        except ImportError:
            print("✗ (not installed)")
            all_ok = False
    
    return all_ok


def check_optional_dependencies() -> None:
    """Check optional dependencies."""
    print("\nChecking optional dependencies:")
    
    optional = [
        ("ray", "Ray (distributed processing)"),
        ("paddleocr", "PaddleOCR (scanned PDF support)"),
    ]
    
    for module, name in optional:
        print(f"  {name}...", end=" ")
        try:
            __import__(module)
            print("✓")
        except ImportError:
            print("○ (not installed, optional)")
        except Exception as e:
            print(f"○ (error: {type(e).__name__})")
    
    # Check Nougat separately due to albumentations compatibility issues
    print(f"  Nougat (math extraction)...", end=" ")
    try:
        # Only check if module exists, don't fully import
        import importlib.util
        spec = importlib.util.find_spec("nougat")
        if spec is not None:
            print("✓ (installed, may have compatibility warnings)")
        else:
            print("○ (not installed, optional)")
    except Exception as e:
        print(f"○ ({type(e).__name__})")


def check_gpu() -> None:
    """Check GPU availability."""
    print("\nChecking GPU:")
    try:
        import torch
        if torch.cuda.is_available():
            device_name = torch.cuda.get_device_name(0)
            print(f"  CUDA available: ✓ ({device_name})")
        else:
            print("  CUDA available: ○ (CPU mode will be used)")
    except ImportError:
        print("  CUDA check: ○ (PyTorch not installed)")


def check_configuration() -> bool:
    """Check configuration."""
    print("\nChecking configuration:")
    
    try:
        from pdf2tex.config import Settings
        settings = Settings()
        print("  Settings loaded: ✓")
        
        # Check HuggingFace token (at top level)
        if settings.huggingface_token:
            print("  HuggingFace API token: ✓")
        else:
            print("  HuggingFace API token: ○ (not set, required for LLM)")
        
        # Check Qdrant (at top level)
        print(f"  Qdrant URL: {settings.qdrant_url}")
        
        return True
    except Exception as e:
        print(f"  Settings error: ✗ ({e})")
        return False


def check_services() -> None:
    """Check external services."""
    print("\nChecking external services:")
    
    # Check Qdrant
    print("  Qdrant connection...", end=" ")
    try:
        from qdrant_client import QdrantClient
        from pdf2tex.config import Settings
        settings = Settings()
        client = QdrantClient(url=settings.qdrant_url)
        client.get_collections()
        print("✓")
    except Exception as e:
        print(f"○ (not available: {e})")
    
    # Check HuggingFace API
    print("  HuggingFace API...", end=" ")
    try:
        from pdf2tex.config import Settings
        settings = Settings()
        if settings.huggingface_token:
            import requests
            resp = requests.get(
                f"https://api-inference.huggingface.co/models/{settings.generation.primary_model}",
                headers={"Authorization": f"Bearer {settings.huggingface_token.get_secret_value()}"},
                timeout=10,
            )
            if resp.status_code in (200, 503):  # 503 = model loading
                print("✓")
            else:
                print(f"○ (status {resp.status_code})")
        else:
            print("○ (no token)")
    except Exception as e:
        print(f"○ ({e})")


def main() -> int:
    """Run all checks."""
    print("=" * 60)
    print("PDF2TeX Installation Validator")
    print("=" * 60)
    
    checks_passed = True
    
    if not check_python_version():
        checks_passed = False
    
    if not check_dependencies():
        checks_passed = False
    
    check_optional_dependencies()
    check_gpu()
    
    if not check_configuration():
        checks_passed = False
    
    check_services()
    
    print("\n" + "=" * 60)
    if checks_passed:
        print("Status: Ready to use! ✓")
        print("Run 'pdf2tex convert <pdf_file>' to convert a PDF.")
        return 0
    else:
        print("Status: Some required components missing ✗")
        print("Please install missing dependencies.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
