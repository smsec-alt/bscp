import os
import warnings
import numpy as np
import pandas as pd
import streamlit as st
from resources import process_df, get_seasonality_chart, get_daily_chart

warnings.simplefilter(action='ignore', category=pd.errors.PerformanceWarning)
st.set_page_config(page_title="Black Sea Cash Prices", layout='wide')

PATH_DATA = r"/Users/semen/Desktop/data/Vitol/TBD/Devs/SNDs/Wheat/Russia/cpt/cash_prices_daily/output"

def main():
    cpt_path = os.path.join(PATH_DATA, 'cpt.parquet.gzip')
    df_cpt = process_df(cpt_path)   
    
    with st.sidebar:
        comm_list = ['Wheat', 'Barley', 'Corn', 'Sunflower', 'Rapeseed']
        comm = st.selectbox("Crop", comm_list)
        df1_cpt = df_cpt.loc[(df_cpt['comm']==comm)]

        country_list = df1_cpt['country'].unique()
        country = st.selectbox("Country", country_list)
        df1_cpt = df1_cpt.loc[(df1_cpt['country']==country)]

        region_list = list(df1_cpt['region'].unique())
        regions = st.multiselect("Regions", region_list, default=region_list[0])
        df1_cpt = df1_cpt.loc[(df1_cpt['region'].isin(regions))]

        comm_class_list = df1_cpt['comm_class'].unique()
        if 1 in df1_cpt['description'].unique():
            comm_class_list = np.append(comm_class_list, 'Wheat 12.5 pro')
        
        comm_class = st.selectbox("Crop Class", comm_class_list)
        if comm_class != 'Wheat 12.5 pro':
            df1_cpt = df1_cpt.loc[(df1_cpt['comm_class']==comm_class)]
        else:
            df1_cpt = df1_cpt.loc[(df1_cpt['description']==1)]

        if country == 'Russia':
            currency = st.selectbox("Currency", ['RUB', 'USD'])
        else:
            currency = 'UAH'
           
        include_company = st.checkbox('Select Specific Company')
        if include_company:
            company_list = list(df1_cpt['company'].unique())
            companies = st.multiselect("Company", company_list, default=company_list[0])
            df1_cpt = df1_cpt.loc[(df1_cpt['company'].isin(companies))]
            
        if (currency == 'RUB') | (currency == 'UAH'):
            df1_cpt = df1_cpt.groupby(['date', 'new_date', 'year'], as_index=False)['price'].median()
        else:
            df1_cpt = df1_cpt.groupby(['date', 'new_date', 'year'], as_index=False)['price_usd'].median()
            df1_cpt.rename({'price_usd':'price'}, axis=1, inplace=True)
            
    st.markdown(f"""#### CPT Prices in {country}""")
    
    title = f"{comm_class} - {', '.join(regions)}"
    fig = get_seasonality_chart(df1_cpt, title, currency)
    fig2 = get_daily_chart(df1_cpt, title, currency)
    st.plotly_chart(fig, use_container_width=True, height=800)
    st.plotly_chart(fig2, use_container_width=True, height=800)
    

if __name__ == '__main__':
    main()
