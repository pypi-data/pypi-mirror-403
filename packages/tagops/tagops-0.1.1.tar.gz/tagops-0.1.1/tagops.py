import sys
from .main import main

def cli():
    if len(sys.argv) > 1 and sys.argv[1] == 'aws':
        main()
    else:
        print("Usage: tagops aws")
        sys.exit(1)
