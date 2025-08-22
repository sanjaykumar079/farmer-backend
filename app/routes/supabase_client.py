import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Load .env variables
load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

if not url or not key:
    raise RuntimeError("Set SUPABASE_URL and SUPABASE_KEY in your environment")

supabase: Client = create_client(url, key)
