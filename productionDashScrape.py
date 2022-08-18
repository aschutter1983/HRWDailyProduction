import streamlit as st
import pandas as pd
import pyodbc
from datetime import datetime, timedelta
import plotly.express as px
from PIL import Image
import time

#determine current time and what shift is going
#this is important as 2nd shift runs into next day

def get_time_filter (cur_time):
    if int(cur_time.strftime("%H")) > 4:
        return datetime.today().strftime("%m/%d/%Y")
    else:
        return (datetime.today() - timedelta(days=1)).strftime("%m/%d/%Y")

def space(num_lines=1):
    """Adds empty lines to the Streamlit app."""
    for _ in range(num_lines):
        st.write("")
     
#Load data from server sql     
# sql_conn = pyodbc.connect(
#                 "DRIVER={SQL Server};SERVER="
#                 + st.Secrets["server"]
#                 + ";DATABASE="
#                 + st.Secrets["database"]
#                 + ";UID="
#                 + st.Secrets["username"]
#                 + ";PWD" 
#                 + st.Secrets["password"]
#                 + ";Trusted_Connection=yes"
#             )

sql_conn = pyodbc.connect("DRIVER={SQL Server};SERVER=10.1.0.33;DATABASE=productionScrap,uid=aschutter;pwd=Freckles01;Trusted_Connection=yes;")

query_prod = f'SELECT * FROM productionData WHERE createdOn >= CAST(\'{get_time_filter(datetime.now())}\' AS DATE)'
query_scrap = f'SELECT DISTINCT ProductionScrap.dbo.scrapData.*, M2MDATA03.dbo.ladetail.fpro_id \
                    FROM ProductionScrap.dbo.scrapData INNER JOIN M2MDATA03.dbo.ladetail \
                    ON ProductionScrap.dbo.scrapData.fjobno = M2MDATA03.dbo.ladetail.fjobno \
                    WHERE createdOn >= CAST(\'{get_time_filter(datetime.now())}\' AS DATE)'

df_production_today = pd.read_sql(query_prod, sql_conn)
df_production_today['Type']='Production'
df_scrap_today =pd.read_sql(query_scrap, sql_conn)
df_scrap_today['Type']='Scrap'
#rename fpro_id col
df_scrap_today.rename(columns={'fpro_id': 'workCenter','scrapQty':'Qty'}, inplace=True)
df_production_today.rename(columns={'productionQty':'Qty'}, inplace=True)
df_totals = pd.concat([df_production_today,df_scrap_today], axis=0)

df_totals['Qty'] = pd.to_numeric(df_totals['Qty'])
df_totals['workCenter'] = pd.to_numeric(df_totals['workCenter']).apply(str)
#setup streamlit page
image = Image.open("hrwLogo_white.png")
st.set_page_config(
    page_title="HRW Production",
    layout='wide',
)

st.markdown(
    """
    <style>
        .main {background-color: #282822;}
    </style>
    """,
    unsafe_allow_html=True
)

#page layout
header = st.container()
overview = st.container()
scrap_wc = st.container()

with header:
    st.markdown(
    """
    <h1 style='text-align: center', 'display: inline-block', 'line-height: unset'>
        <img src ="https://huskyrackandwire.com/wp-content/themes/husky-rack-wire/images/logo.svg" style='float: left', 'vertical-align: middle'>Daily Production Overview
    </h1>
    """,
    unsafe_allow_html=True
    )
    #![HRW Image](https://huskyrackandwire.com/wp-content/themes/husky-rack-wire/images/logo.svg) <h1 style='text-align: center'> RollForming Daily Production</h1>
    #st.image(image,width=250)
    #st.title("RollForming Daily Production")
    
with overview:
    st.markdown(
    """
    <style>
        [data-testid="metric-container"] {
            border: 4px solid green;
            border-radius: 30px;

        }
        [data-testid="stMetricValue"] {
            padding: 10px;
            text-align: center;
            width: fit-content;
            margin: auto;
        }
        [data-testid="stMetricLabel"] {
            text-align: center;
            width: fit-content;
            margin: auto;
        }
        [data-testid="stHeader"] {
            background-color: rgba(0,0,0,0);
        }
    </style>
    """,
    unsafe_allow_html=True
    )
    st.title("")
    b1,b2,b3= st.columns(3)

    production = df_production_today['Qty'].sum()
    scrap = int(pd.to_numeric(df_scrap_today['Qty']).sum())
    rate = round((scrap / production)*100,1)

    b1.metric(label="Current Production",value=f"{production} ft")
    b2.metric(label="Current Scrap", value= f"{scrap} ft")
    b3.metric(label="Overall Scrap Rate",value=f"{rate}%")

    with scrap_wc:
        st.header("Totals by Workcenter")
        fig = px.histogram(df_totals, x='workCenter',
            y='Qty',color='Type',
            height=400,
            barmode='group')
        st.plotly_chart(fig,use_container_width=True)

    time.sleep(60)
    st.experimental_rerun()
