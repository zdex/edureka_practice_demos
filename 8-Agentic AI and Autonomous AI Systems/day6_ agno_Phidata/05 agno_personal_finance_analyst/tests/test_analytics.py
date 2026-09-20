from pathlib import Path
from src.analytics import finance_snapshot, category_spending, monthly_summary
from src.categorizer import add_categories
from src.data_loader import load_sample

def _sample():
    p=Path(__file__).resolve().parents[1]/'sample_data'/'sample_transactions.csv'
    return add_categories(load_sample(p),'unused',use_embeddings=False)

def test_snapshot_is_consistent():
    s=finance_snapshot(_sample())
    assert s['total_income']>0 and s['total_expenses']>0
    assert round(s['total_income']-s['total_expenses'],2)==s['net_cash_flow']

def test_categories_exist():
    assert len(category_spending(_sample()))>0

def test_two_months_present():
    assert len(monthly_summary(_sample()))>=2
