import os, uuid
import pandas as pd
import streamlit as st
from src.agent_team import build_finance_team
from src.analytics import category_spending, deterministic_report, finance_snapshot, monthly_summary, recurring_transactions, unusual_transactions
from src.categorizer import add_categories
from src.config import settings
from src.data_loader import load_sample, load_transactions
from src.reporting import report_to_dict

st.set_page_config(page_title='Agno Personal Finance Analyst', page_icon='💰', layout='wide')
st.title('Agno Personal Finance Analyst')
st.caption('Agno multi-agent team + Gemini free tier + local Hugging Face embeddings')

with st.sidebar:
    st.header('1. Model setup')
    api_key = st.text_input('Google AI Studio API key', type='password', value=os.getenv('GOOGLE_API_KEY',''))
    st.text_input('Gemini model', value=settings.gemini_model, disabled=True)
    st.text_input('Embedding model', value=settings.hf_embedding_model, disabled=True)
    st.header('2. Data')
    source = st.radio('Choose input', ['Classroom sample','Upload CSV/XLSX'])
    uploaded = st.file_uploader('Bank transaction export', type=['csv','xlsx','xls']) if source!='Classroom sample' else None
    use_embeddings = st.checkbox('Auto-categorize with local embeddings', value=True)
    currency = st.selectbox('Currency symbol',['₹','$','€','£'])
    debug_mode = st.checkbox('Show Agno debug/member responses', value=False)
    fallback_allowed = st.checkbox('Use deterministic fallback if API quota fails', value=True)

try:
    df = load_sample() if source=='Classroom sample' else load_transactions(uploaded) if uploaded else None
    if df is None:
        st.info('Upload a CSV/XLSX file, or switch to Classroom sample.'); st.stop()
    with st.spinner('Categorizing transactions...'):
        df = add_categories(df, settings.hf_embedding_model, use_embeddings=use_embeddings)
except Exception as e:
    st.error(f'Could not load/categorize data: {e}'); st.stop()

snap = finance_snapshot(df)
c1,c2,c3,c4 = st.columns(4)
c1.metric('Income',f"{currency}{snap['total_income']:,.0f}")
c2.metric('Expenses',f"{currency}{snap['total_expenses']:,.0f}")
c3.metric('Net cash flow',f"{currency}{snap['net_cash_flow']:,.0f}")
c4.metric('Savings rate',f"{snap['savings_rate_percent']:.1f}%")

t1,t2,t3,t4 = st.tabs(['Transactions','Deterministic analytics','Agno team','How it works'])
with t1:
    d=df.copy(); d['date']=d['date'].dt.date; st.dataframe(d,width=True,hide_index=True)
with t2:
    a,b=st.columns(2)
    with a:
        st.subheader('Spending by category'); cats=pd.DataFrame(category_spending(df))
        if not cats.empty: st.bar_chart(cats.set_index('category')[['amount']]); st.dataframe(cats,hide_index=True,width=True)
        st.subheader('Recurring candidates'); rec=pd.DataFrame(recurring_transactions(df)); st.dataframe(rec,hide_index=True,width=True) if not rec.empty else st.write('None detected.')
    with b:
        st.subheader('Monthly trend'); m=pd.DataFrame(monthly_summary(df)); st.dataframe(m,hide_index=True,width=True)
        if not m.empty: st.line_chart(m.set_index('month')[['income','expenses']])
        st.subheader('Transactions to review'); u=pd.DataFrame(unusual_transactions(df)); st.dataframe(u,hide_index=True,width=True) if not u.empty else st.write('None detected.')
    st.caption('Arithmetic/statistics are deterministic Python tools; the LLM interprets results.')
with t3:
    st.write('Five specialists: Transaction Analyst, Spending Pattern Analyst, Unusual Transaction Reviewer, Budget Advisor, Finance Coach.')
    goal=st.text_area('Team goal', value='Analyze these transactions. Explain cash flow, spending patterns, what deserves attention, unusual transactions to manually review, and a practical plan for next month.')
    if st.button('Run Agno Finance Team',type='primary',width=True):
        if not api_key: st.warning('Enter a free Google AI Studio API key.')
        else:
            os.environ['GOOGLE_API_KEY']=api_key
            sid=st.session_state.setdefault('session_id',str(uuid.uuid4()))
            try:
                with st.spinner('Agno is coordinating the specialist agents...'):
                    r=build_finance_team(df,debug_mode).run(goal,user_id='classroom-user',session_id=sid)
                st.session_state['latest_report']=report_to_dict(r.content); st.session_state['report_source']='Agno + Gemini'
            except Exception as e:
                if fallback_allowed:
                    st.warning('Gemini request failed or hit a free-tier limit. Showing deterministic fallback.'); st.code(str(e))
                    st.session_state['latest_report']=deterministic_report(df,currency); st.session_state['report_source']='Deterministic fallback'
                else: st.error(str(e))
    report=st.session_state.get('latest_report')
    if report:
        st.success('Report source: '+st.session_state.get('report_source','Unknown'))
        st.subheader('Executive summary'); st.write(report.get('executive_summary',''))
        x,y=st.columns(2)
        with x:
            st.markdown('### Positives'); [st.write('• '+z) for z in report.get('positives',[])]
            st.markdown('### Needs attention'); [st.write('• '+z) for z in report.get('needs_attention',[])]
            st.markdown('### Monthly observations'); [st.write('• '+z) for z in report.get('monthly_observations',[])]
        with y:
            st.markdown('### Transactions to review'); [st.write('• '+z) for z in report.get('unusual_transactions',[])]
            st.markdown('### Next-month actions'); [st.write(f'{i}. {z}') for i,z in enumerate(report.get('budget_actions',[]),1)]
            st.markdown('### Savings target'); st.write(report.get('savings_target',''))
        st.info(report.get('disclaimer',''))
with t4:
    st.code('''CSV/XLSX -> normalize -> local HF embeddings -> categories\n                 |\n                 +-> deterministic Python tools\n                           |\n                     Agno Team Leader\n                       /   |   \\\n              specialist agents\n                           |\n                     FinanceReport''')
    st.markdown('**Teaching split:** Python = calculation; Gemini = interpretation; Agno = orchestration; Hugging Face = local semantic embeddings.')
st.divider(); st.caption('Educational budgeting demo only; not financial, investment, tax, legal, insurance, or credit advice.')
