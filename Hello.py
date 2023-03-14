import warnings
import numpy as np
import pandas as pd
import streamlit as st
from gcs import GCS
from resources import process_df, get_seasonality_chart, get_daily_chart, rus_regions_mapping, summary_df, export_tax_dict
warnings.simplefilter(action='ignore', category=pd.errors.PerformanceWarning)

st.set_page_config(page_title="Black Sea Cash Prices", layout='wide')


with st.sidebar:
    country = st.selectbox("Country", ['Russia', 'Ukraine'])
    price_col = 'price'
    if country == 'Russia':
        currency = st.selectbox("Currency", ['RUB', 'USD'])
        price_col = 'price' if currency == 'RUB' else 'price_usd'
    else:
        currency = 'UAH'

def main():
    gcs = GCS('sm_data_bucket', streamlit=True)

    df_temp = gcs.read_parquet('russia_cash_price/cpt.parquet.gzip')
    df_ozk = gcs.read_parquet('russia_cash_price/ozk.parquet.gzip')
    print(df_ozk)
    df = process_df(df_temp)   
    df_tax = gcs.read_csv('russia_cash_price/Export_Tax.csv', parse_dates=['date'])


    last_tax = df_tax.loc[(df_tax['date']==df_tax['date'].max()) & (df_tax['grain']=='Wheat')& (df_tax['variable']=='tax')]['value'].values[0]

    # SUMMARY TABLE
    df_pivot = summary_df(df, last_tax, country)
    st.markdown(df_pivot.to_html(), unsafe_allow_html=True)
    st.markdown('')

    df_sub = df.loc[(df['country']==country)][['date', 'new_date', 'year', 'company', 'comm','comm_class', 'region',price_col]]
    df_sub.rename({price_col:'price'}, axis=1, inplace=True)
    if country == 'Russia':
        df_sub['major_region'] = np.where(df_sub['region'].isin(rus_regions_mapping.keys()),
                                        df_sub['region'].replace(rus_regions_mapping), 'Rest')
    else:
        df_sub['major_region'] = country
            
    st.markdown(f"""#### Seasonality Charts """)
    df_summary = df_sub.loc[(df_sub['major_region'].isin(['South', country])) & (df_sub['company']!='Demetra')]
    df_charts = df_summary.groupby(['date', 'new_date', 'year', 'comm_class'], as_index=False)['price'].median()
    con1 = st.container()
    col1, col2 = con1.columns(2)
    if country == 'Russia':
        fig1 = get_seasonality_chart(df_charts.query('comm_class=="Wheat 3 Grade"'), 'Wheat 3 Grade - South, Russia', currency)
        fig2 = get_seasonality_chart(df_charts.query('comm_class=="Wheat 4 Grade"'), 'Wheat 4 Grade - South, Russia', currency)
        fig3 = get_seasonality_chart(df_charts.query('comm_class=="Wheat 5 Grade"'), 'Wheat 5 Grade - South, Russia', currency)
        fig4 = get_seasonality_chart(df_charts.query('comm_class=="Wheat Feed"'), 'Wheat Feed - South, Russia', currency)
        col1.plotly_chart(fig2, use_container_width=True, height=800)
        col2.plotly_chart(fig1, use_container_width=True, height=800)
        col1.plotly_chart(fig3, use_container_width=True, height=800)
        col2.plotly_chart(fig4, use_container_width=True, height=800)

        con2 = st.container()
        con2.markdown(f"""#### CPT Spreads in {country}""")
        col3, col4 = con2.columns(2)
        item1 = col3.selectbox("Crop 1", ['Wheat 3 Grade', 'Wheat Feed', 'Wheat 4 Grade', 'Wheat 5 Grade', 'Barley', 'Corn', 'Sunflower', 'Rapeseed'])
        item2 = col4.selectbox("Crop 2", ['Wheat Feed', 'Wheat 3 Grade', 'Wheat 4 Grade', 'Wheat 5 Grade', 'Barley', 'Corn', 'Sunflower', 'Rapeseed'])
        df_spreads = df_charts.loc[df_charts['comm_class'].isin([item1, item2])].pivot(index=['year', 'date', 'new_date'], columns='comm_class', values='price')
        df_spreads['price'] = df_spreads[item1] - df_spreads[item2]
        df_spreads.reset_index(inplace=True)
        df_spreads = df_spreads.dropna()
        fig5 = get_seasonality_chart(df_spreads, f'{item1} - {item2}, South Russia', currency)
        fig6 = get_daily_chart(df_spreads, f'{item1} - {item2}, South Russia', currency)
        col3.plotly_chart(fig5, use_container_width=True, height=800)
        col4.plotly_chart(fig6, use_container_width=True, height=800)

        con3 = st.container()
        con3.markdown(f"""#### Export Tax & FOB Implied""")
        col3_1, col4_1 = con3.columns(2)
        df_tax['year'] = df_tax['date'].dt.year
        df_tax['new_date'] = df_tax['date'] + pd.DateOffset(year=2020)
        grain = col3_1.selectbox("Crop", ['Wheat', 'Barley', 'Corn'])
        variable = col4_1.selectbox("Variable", ['Export Tax, USD', 'Export Tax, RUB', 'Export Tax Index'])
        df_plot = df_tax.loc[(df_tax['grain']==grain)&(df_tax['variable']==export_tax_dict[variable])]
        fig_tax_1 = get_seasonality_chart(df_plot, f'{grain} - {variable}', '','value', '')

        df_fob_tax = df_tax.loc[(df_tax['grain']==grain)&(df_tax['variable']=='tax')]
        df_cpt_fob = df.loc[(df['region']=='Krasnodar') & (df['company'].isin(['Rif', 'Aston'])) & (df['date']>pd.Timestamp('2021-04-01'))]
        if grain == 'Wheat':
            df_cpt_fob = df_cpt_fob.loc[df['description']==1]
        else:
            df_cpt_fob = df_cpt_fob.loc[df['comm']==grain]

        df_cpt_fob = df_cpt_fob.groupby(['date', 'new_date', 'year'], as_index=False)['price_usd'].mean()
        df_fob = df_cpt_fob.merge(df_fob_tax[['date', 'new_date', 'year', 'value']], on=['date', 'new_date', 'year'], how='left')
        df_fob['value'] = df_fob['value'].fillna(method='ffill')
        df_fob['price'] = df_fob['price_usd']+df_fob['value']+25
        if grain == 'Wheat':
            df_fob = df_ozk
        fig_tax_2 = get_seasonality_chart(df_fob, f'{grain} - FOB Implied', 'USD', y_axis_name='FOB Implied')
        col3_1.plotly_chart(fig_tax_1, use_container_width=True, height=800)
        col4_1.plotly_chart(fig_tax_2, use_container_width=True, height=800)


        exp = st.expander(" CPT Regional Spreads")
        col5, col6, _ = exp.columns(3)
        crop = 'Wheat 4 Grade'
        region1 = col5.selectbox("Region 1", ['South', 'Central', 'Volga'])
        region2 = col6.selectbox("Region 2", ['Central', 'South', 'Volga'])
        df_regions = df_sub.loc[(df_sub['major_region'].isin([region1, region2])) & (df_sub['comm_class']==crop) & (df_sub['company']=='Demetra')]
        df_regions = df_regions.groupby(['date', 'new_date', 'year', 'major_region'], as_index=False)['price'].median()
        df_regions = df_regions.pivot(index=['year', 'date', 'new_date'], columns='major_region', values='price')
        df_regions['price'] = df_regions[region1] - df_regions[region2]
        df_regions.reset_index(inplace=True)
        df_regions = df_regions.dropna()
        df_regions = df_regions[df_regions['date']>pd.Timestamp('2022-1-1')]
        fig7 = get_daily_chart(df_regions, f'{region1} - {region2}, {crop}', currency)
        exp.plotly_chart(fig7, use_container_width=True, height=800)

    else:
        fig1 = get_seasonality_chart(df_charts.query('comm_class=="Wheat 2 Grade"'), 'Wheat 2 Grade, Ukraine', currency)
        fig2 = get_seasonality_chart(df_charts.query('comm_class=="Corn"'), 'Corn, Ukraine', currency)    
        col1.plotly_chart(fig1, use_container_width=True, height=800)
        col2.plotly_chart(fig2, use_container_width=True, height=800)

    

if __name__ == '__main__':
    main()
