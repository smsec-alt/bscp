import warnings
import numpy as np
import pandas as pd
import streamlit as st
from gcs import GCS
from resources import process_df, get_seasonality_chart, get_daily_chart, get_freight_chart

warnings.simplefilter(action='ignore', category=pd.errors.PerformanceWarning)
st.set_page_config(page_title="Black Sea Cash Prices", layout='wide')


def main():
    gcs = GCS('sm_data_bucket', streamlit=True)

    df_temp = gcs.read_parquet('russia_cash_price/cpt.parquet.gzip')
    df_freight = gcs.read_csv('russia_cash_price/freight.csv', parse_dates=['delivery_time.from'])
    df_cpt = process_df(df_temp)   
   
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
    if country == 'Russia':
        con1 = st.container()
        con1.markdown(f"""#### Truck costs""")
        col1, col2 = con1.columns(2)
        fig3 = get_freight_chart(df_freight, regions, 'direction.from.region')
        fig4 = get_freight_chart(df_freight, regions, 'direction.to.region')
        col1.plotly_chart(fig3, use_container_width=True, height=800)
        col2.plotly_chart(fig4, use_container_width=True, height=800)
    

if __name__ == '__main__':
    main()
