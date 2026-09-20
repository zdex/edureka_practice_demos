import os, uuid
from src.agent_team import build_finance_team
from src.categorizer import add_categories
from src.config import settings
from src.data_loader import load_sample

if not os.getenv('GOOGLE_API_KEY'):
    raise SystemExit('Set GOOGLE_API_KEY in .env or your environment.')
df=add_categories(load_sample(),settings.hf_embedding_model,True)
r=build_finance_team(df,True).run('Analyze my spending and give me a practical next-month budget plan.',user_id='cli-demo',session_id=str(uuid.uuid4()))
print(r.content.model_dump_json(indent=2) if hasattr(r.content,'model_dump_json') else r.content)
