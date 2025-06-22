import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from modules.html_learning import get_context_keywords

if __name__ == "__main__":
    keywords = get_context_keywords()
    print("最終的な context_keywords =", keywords)
