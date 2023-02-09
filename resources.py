import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

export_tax_dict = {'Export Tax Index': 'index', 'Export Tax, USD':'tax', 'Export Tax, RUB':'tax_rub'}

rus_regions_mapping = {'Krasnodar': 'South', 'Rostov':'South',
                       'Voronezh': 'Central', 'Saratov':'Volga', 'Tambov':'Central',
                       'Belgorod': 'Central', 'Bashkortostan':'Volga',
                       'Kursk': 'Central', 'Oryol': 'Central', 'Tula':'Central',
                       'Samara':'Volga', 'Volgograd': 'Central'}


# def process_df(df_path:str)->pd.DataFrame:
def process_df(df_cpt:pd.DataFrame)->pd.DataFrame:

    # df_cpt = pd.read_parquet(df_path)
    df_cpt['region'] = df_cpt['region'].str.title()
    df_cpt['comm'] = df_cpt['comm_class']
    df_cpt['comm'] = np.where(df_cpt['comm'].isin(['Wheat 3 Grade', 'Wheat 4 Grade', 'Wheat 5 Grade', 'Wheat Durum', 'Wheat Feed', 'Wheat 2 Grade']), 'Wheat', df_cpt['comm'])
    df_cpt.drop('usd', axis=1, inplace=True)
    df_cpt['new_date'] = df_cpt['date']+pd.DateOffset(year=2020)
    df_cpt = df_cpt[df_cpt['year']>2018]
    return df_cpt


def summary_df(df:pd.DataFrame, last_tax: int, country: str):
    df_sub = df.loc[(df['country']==country)]
    last_date = df_sub['date'].max()
    yday_date = df_sub[df_sub['date']<last_date]['date'].max()
    weekago_date = df_sub[df_sub['date']<=last_date-pd.DateOffset(days=7)]['date'].max()
    df_sub = df_sub.loc[df_sub['date'].isin([last_date, yday_date, weekago_date])]
    df_sub['date'] = df_sub['date'].replace({last_date:'Today', yday_date:'Yesterday', weekago_date:'Last Week'})
    if country == 'Russia':
        df_sub['major_region'] = np.where(df_sub['region'].isin(rus_regions_mapping.keys()),
                                        df_sub['region'].replace(rus_regions_mapping), 'Rest')
        df_sub = df_sub.loc[(df_sub['company'].isin(['Aston', 'Rif'])) 
                            & (df_sub['comm_class'].isin(['Wheat 4 Grade', 'Wheat 3 Grade', 'Wheat 5 Grade'])) 
                            & (df_sub['major_region']=='South')]
        df_sub['comm_class'] = np.where(df_sub['description']==1, 'Wheat 12.5 pro', df_sub['comm_class'])
        currency = 'RUB'
    else:
        df_sub = df_sub.loc[(df_sub['comm_class'].isin(['Wheat 2 Grade', 'Corn'])) 
                            & (df_sub['company'].isin(['Nibulon']))]
        df_sub['major_region'] = country
        currency = 'UAH'
        
    df_pivot = df_sub.pivot(index=['comm_class', 'region', 'company'], columns='date', values=['price', 'price_usd'])
    df_pivot[('price', 'DoD')] = df_pivot[('price', 'Today')]-df_pivot[('price', 'Yesterday')]
    df_pivot[('price', 'WoW')] = df_pivot[('price', 'Today')]-df_pivot[('price', 'Last Week')]
    df_pivot[('price_usd', 'DoD')] = df_pivot[('price_usd', 'Today')]-df_pivot[('price_usd', 'Yesterday')]
    df_pivot[('price_usd', 'WoW')] = df_pivot[('price_usd', 'Today')]-df_pivot[('price_usd', 'Last Week')]

    df_pivot = df_pivot[[('price','Today'), ('price','Yesterday'), ('price','Last Week'), ('price','DoD'), ('price','WoW'),
                        ('price_usd','Today'), ('price_usd','Yesterday'), ('price_usd','Last Week'), ('price_usd','DoD'), ('price_usd','WoW')]]
    df_pivot.rename({'price_usd':'USD', 'price':currency}, axis=1, inplace=True)
    df_pivot = df_pivot.rename_axis([None, None, None], axis=0)
    df_pivot = df_pivot.rename_axis((None, None), axis=1)

    if country=='Russia':
        # last_tax = df_tax.loc[(df_tax['date']==df_tax['date'].max()) & (df_tax['grain']=='Wheat')& (df_tax['variable']=='tax')]['value'].values[0]
        df_pivot[('FOB', 'Implied')]=df_pivot[('USD', 'Today')]+25+last_tax
    
      # To get the id of the latest row with level 0
    df_index = df_pivot.reset_index().iloc[:,:3].copy()
    df_index.columns = ['level_0', 'level_1', 'level_2']
    df_index = df_index.drop_duplicates(subset='level_0', keep='last')
    index_list = list(df_index.itertuples(index=False, name=None))
    
    def make_pretty(styler):
      def highlight_negative(x): 
          return np.where(x<0, f"color: red;background-color: #ffe6e6", None) 
      def highlight_positive(x): 
          return np.where(x>0, f"color: green;background-color: #e6ffe6", None) 

      styler.set_table_styles([{'selector': 'th.col_heading, th, tr, td', 'props': 'text-align: center;border-style: none;'},
                               {'selector': 'th.col_heading.level0', 'props': 'font-size: 1.1em;'},
                               {'selector': 'th.row_heading.level0','props': 'text-align: center;'},
                               {'selector': 'td:hover, tr:hover', 'props': 'background-color: #F8F8F8; color:black;'},
                               ])
      # vertical borders
      styler.set_table_styles({('USD', 'Today'): [{'selector': 'th, td', 'props': 'border-left: 1px dashed #C0C0C0'}],
                               (currency, 'Today'): [{'selector': 'th, td', 'props': 'border-left: 1px dashed #C0C0C0'}],
                               ('FOB', 'Implied'): [{'selector': 'th, td', 'props': 'border-left: 1px dashed #C0C0C0'}],
                               }, overwrite=False, axis=0)
      # horizontal borders
      styler.set_table_styles({row: [{'selector': '', 'props': 'border-bottom: 1px dashed #C0C0C0'}] for row in index_list},
                              overwrite=False, axis=1)
      
      styler.set_caption("CPT Matrix").set_table_styles([{ 'selector': 'caption', 'props': 'caption-side: top; font-size:1.1em; font-style: italic;'}], overwrite=False)
      styler.set_properties(**{'background-color': 'white', 'font-weight': '10pt'})
      styler.background_gradient(axis=0, cmap="Blues", subset=[(currency,'Today'),('USD','Today')])
      styler.apply(highlight_negative, subset=[(currency,'DoD'),(currency,'WoW'),('USD','DoD'),('USD','WoW')])
      styler.apply(highlight_positive, subset=[(currency,'DoD'),(currency,'WoW'),('USD','DoD'),('USD','WoW')])
      styler.format('{:,.0f}')
      if country == 'Ukraine':
        styler.hide([('USD', 'Today'), ('USD', 'Yesterday'), ('USD', 'Last Week'),
         ('USD', 'DoD'), ('USD', 'WoW')], axis='columns')

      return styler

    
    s = df_pivot.style.pipe(make_pretty)

    
    return s


def get_seasonality_chart(df: pd.DataFrame, title: str, currency: str, y_axis='price', y_axis_name='Price CPT')->px.line:
      last_year = df['year'].max()
      y_axis_name = f'{y_axis_name}, {currency}' if currency!= None else y_axis_name
      fig = px.line(df[df['year']<(last_year-1)], x='new_date', y=y_axis,
                  color_discrete_sequence=px.colors.qualitative.G10, color='year',
                  labels={'new_date':'', 'year':'Year', y_axis: y_axis_name}
                  )
      fig.update_traces(line=dict(width=1))
      fig.add_trace(go.Scatter(x=df[df['year']==last_year-1]['new_date'],
                                  y=df[df['year']==last_year-1][y_axis],
                                  fill=None, name=str(last_year-1), mode='lines',
                                  line=dict(color='black', width=2)))
      fig.add_trace(go.Scatter(x=df[df['year']==last_year]['new_date'],
                                  y=df[df['year']==last_year][y_axis],
                                  fill=None, name=str(last_year), mode='lines+markers',
                                  line=dict(color='firebrick', width=2)))

      fig.update_layout(legend={'traceorder': 'reversed'}, title=title,
                        hovermode="x unified", font=dict(color='rgb(82, 82, 82)', family='Arial'),
                          xaxis=dict(gridcolor='#FFFFFF',tickformat="%b %d",
                                      linecolor='rgb(204, 204, 204)', linewidth=1, ticks='outside',
                                      tickfont=dict(size=12)),
                          yaxis=dict(gridcolor='#F8F8F8', tickfont=dict(size=12)),
                          plot_bgcolor='white')
      return fig


def get_daily_chart(df: pd.DataFrame, title: str, currency: str, y_axis='price', y_axis_name='Price CPT')->px.line:
      fig = px.line(df, x='date', y=y_axis,
                  color_discrete_sequence=px.colors.qualitative.G10, 
                  labels={'date':'', 'year':'Year', y_axis:f'{y_axis_name}, {currency}'}
                  )
      fig.update_layout(legend={'traceorder': 'reversed'}, title=title,
                        hovermode="x unified", font=dict(color='rgb(82, 82, 82)', family='Arial'),
                          xaxis=dict(gridcolor='#FFFFFF',tickformat="%b %Y",
                                      linecolor='rgb(204, 204, 204)', linewidth=1, ticks='outside',
                                      tickfont=dict(size=12)),
                          yaxis=dict(gridcolor='#F8F8F8', tickfont=dict(size=12)),
                          plot_bgcolor='white')
      return fig