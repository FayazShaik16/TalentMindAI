import sys
import os
import asyncio

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.build_embeddings import run_build

def main():
    print("Starting clean vector index rebuild...")
    asyncio.run(run_build(force=True))

if __name__ == "__main__":
    main()
