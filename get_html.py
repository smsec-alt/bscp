import json
import folium
import pandas as pd
from urllib.request import urlopen

def get_shapefile():
    response = urlopen('https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/russia.geojson')
    counties = json.load(response)

    mapping_dict = {
        'Бурятия': 'Республика Бурятия',
        'Тыва': 'Республика Тыва',
        'Ханты-Мансийский автономный округ - Югра': 'Ханты-Мансийский АО',
        'Адыгея':'Республика Адыгея (Адыгея)',
        'Татарстан':'Республика Татарстан (Татарстан)',
        'Марий Эл': 'Республика Марий Эл',
        'Чувашия':'Чувашская Республика - Чувашия',
        'Северная Осетия - Алания':'Республика Северная Осетия-Алания',
        'Алтай':'Республика Алтай',
        'Дагестан':'Республика Дагестан',
        'Ингушетия':'Республика Ингушетия',
        'Башкортостан':'Республика Башкортостан',
        'Чеченская республика':'Чеченская Республика',
        'Удмуртская республика':'Удмуртская Республика',
        'Кемеровская область':'Кемеровская область - Кузбасс',
        'Кабардино-Балкарская республика':'Кабардино-Балкарская Республика',
        'Карачаево-Черкесская республика':'Карачаево-Черкесская Республика',
        'Москва':'Город Москва столица Российской Федерации город федерального значения',
    }

    for k in range(len(counties['features'])):
        counties['features'][k]['id'] = k
        region_name = counties['features'][k]['properties']['name']
        if region_name in mapping_dict:
            counties['features'][k]['properties']['name'] = mapping_dict[region_name]
    return counties


def get_html(subtable, counties):
    def folium_del_legend(choropleth: folium.Choropleth):
        del_list = []
        for child in choropleth._children:
            if child.startswith('color_map'):
                del_list.append(child)
        for del_item in del_list:
            choropleth._children.pop(del_item)
        return choropleth

    russia_map = folium.Map(location=[65,101], tiles='cartodbpositron', zoom_start=3)

    choropleth=folium.Choropleth(geo_data=counties,
                data=subtable, columns = ['Region', 'Value'],name='choropleth',
                key_on='feature.properties.name',
                fill_color='Spectral_r', line_weight=0.5,legend_name='Value',
                nan_fill_color='White', fill_opacity=0.6, highlight=True,
                bins=pd.qcut(subtable['Value'], q=[0,0.05,0.1,0.15,0.3,0.5,0.7,0.85,0.9,0.99,1], retbins=True, duplicates='drop')[1]
                ).add_to(russia_map)

    folium_del_legend(choropleth).add_to(russia_map)

    subtable_indexed = subtable.set_index('Region')
    for s in counties['features']:
        try:
            s['properties']['value'] = subtable_indexed.loc[s['properties']['name'],'Value']
        except:
            s['properties']['value'] = 0
            pass

    choropleth.geojson.add_child(
        folium.features.GeoJsonTooltip(fields=['name_latin', 'value'], 
                                        aliases=['Region', 'Production'],
                                        style=('background-color: white; color: black; border: 2px solid black;border-radius: 3px;box-shadow: 3px;'),
                                        localize=True))
    folium.LayerControl().add_to(russia_map)
    return russia_map


# def main():
#     table = pd.read_excel('Historical_Russian_Production_all_crops_RU.xlsx')
#     table = table[table['Value']!=99999999.90]
#     counties = get_shapefile()
#     item = 'Production'
    
#     for crop in ['Wheat', 'Barley', 'Sunflower', 'Corn', 'Rapeseed']:
#         for year in range(1995, 2022):
#             try:
#                 print(year)
#                 html = get_html(table, counties, item, crop, year)
#                 html.save(f'./html/{crop}_{year}_{item}.html')
#             except:
#                 pass

# if __name__ == '__main__':
#     main()
