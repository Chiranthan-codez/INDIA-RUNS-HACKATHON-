import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

# Forward execution to scripts.rank
from scripts.rank import main

if __name__ == '__main__':
    main()
