import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()
class SupabaseSetup:
    def __init__(self):
        self.url: str = os.environ.get("SUPABASE_URL")
        self.key: str = os.environ.get("SUPABASE_KEY")
        self.supabase: Client = create_client(self.url, self.key)

