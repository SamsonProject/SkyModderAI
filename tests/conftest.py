"""Pytest configuration for SkyModderAI tests."""
import sys
from pathlib import Path

# Add project root to Python path for imports
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))
