import asyncio
import sys
import os
from .lazycook import create_assistant

async def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    
    if not api_key and len(sys.argv) > 1:
        api_key = sys.argv[1]
        
    if not api_key:
        print("Error: GEMINI_API_KEY not found in environment variables.")
        print("Usage: python -m lazycook YOUR_API_KEY")
        sys.exit(1)
        
    # create_assistant returns a MultiAgentAssistantConfig object
    config = create_assistant(api_key)
    # run_cli is an async method of MultiAgentAssistantConfig
    await config.run_cli()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0)
