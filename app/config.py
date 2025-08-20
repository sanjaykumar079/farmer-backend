import os
from dotenv import load_dotenv

load_dotenv()
SUPABASE_URL = "https://kehevazptukiemattuhg.supabase.co"
SUPABASE_KEY = "sb_publishable_Yqn7difLk2cVXdEhyGWMbQ_hWNR6WET"

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# AI keys (if needed)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
