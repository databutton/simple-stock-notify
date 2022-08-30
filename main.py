import databutton as db
import streamlit as st
import pandas as pd
import yfinance as yf
from streamlit_ace import st_ace
from slack import post_message_to_slack
from sympy import *
from sympy.parsing.sympy_parser import parse_expr


@db.apps.streamlit(route="/app", name="Stock alerts")
def hello():
    st.title("Stock alerts")
    
    alerts = db.storage.dataframes.get('alerts')
    st.write('Active alerts')
    st.write(alerts)
    new_alert = st.form(key='stt')
    with new_alert:
        st.write('Add new alert')
        ticker = st.text_input(label="Ticker")
        st.write('Condition')
        value = '''x < 20'''
        condition = st_ace(value=value, theme="nord_dark", language="python", min_lines=2)
        frequency = st.selectbox(label='Check every', options=["5m",  "1h", "4h", "12h", "24h"])
        bt = st.form_submit_button()

        if(bt):
            ix = len(alerts)
            if(ix<1):
                alerts = pd.DataFrame(columns=["Ticker", "Condition", "Frequency", "Last Run"])
            alerts.loc[ix, "Ticker"]    = ticker
            alerts.loc[ix, "Condition"] = condition
            alerts.loc[ix, "Frequency"] = frequency
            alerts.loc[ix, "Last Run"]  = "Never"

            db.storage.dataframes.put(alerts, 'alerts')
            st.write('The new alert has been added')




@db.jobs.repeat_every(seconds=60*5)
def repeating_job():
    alerts = db.storage.dataframes.get('alerts')

    x = Symbol('x')
    for ix, row in alerts.iterrows():
        ticker    = row['Ticker']
        condition = parse_expr(row['Condition'])
        frequency = row['Frequency']
        now   = pd.to_datetime('now', utc=True)
        try:
            lrun  = pd.to_datetime(row['Last Run'], utc=True)
        except:
            lrun = now
        alerts.loc[ix, 'Last Run'] = str(now)
        tdelta = now-lrun
        if(tdelta < pd.to_timedelta(frequency)):
            continue

        # Get the price
        stock = yf.Ticker(ticker)
        price = stock.info['regularMarketPrice']

        if(condition.subs(x, price)):
            text = '''
            * Stock alert *
            An alert just went off
            '''
            post_message_to_slack(text, 'trading', ':see_no_evil:','karper')
        