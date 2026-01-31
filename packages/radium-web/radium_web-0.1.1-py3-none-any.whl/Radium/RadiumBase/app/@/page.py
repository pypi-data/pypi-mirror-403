import json
from Radium.outputs import Outputs
from auth.auth import account
from supabase_utils.setup import SupabaseSetup

def page(req):
     return Outputs.HTMLFileResponse('templates/home.html', )