import requests
import json
import re
from bs4 import BeautifulSoup


class PySimepar:

    def __init__(self, city_code):

        self.city_code = city_code
        self.forecast_url = "https://www.simepar.br/simepar/forecast_by_counties/" + str(self.city_code)

        self.json_re = re.compile(r'.*json.*(\{.*a\>\"\}).*')
        self.forecast_icon_re = re.compile(r'.*wi\s(wi[\w|-]*)\s.*')
        self.forecast_cond_re = re.compile(r'.*title="([\w|\s]*)".*')
        self.forecast_temp_re = re.compile(r'.*data:\s\[([\d,-]*)\].*')
        self.digit_re = re.compile(r'[\d|.]+')
        self.direction_re = re.compile(r'[N|S|L|O|E]+')
        self.tz_fix = 10800

        self.data = { 'current': None, 'hourly': None, 'daily': None }

        self.s = None

    def update(self):

        self.data = { 'current': None, 'hourly': None, 'daily': None }

        try:        
            r = requests.get(self.forecast_url)
            r.encondig="utf-8"
            s = BeautifulSoup(r.text, 'html.parser')
            ji = self.json_re.search(r.text)
            j = json.loads(ji.groups()[0]) 
            forecast_list = []
            #for i in sorted(j.keys()):
            for i in j.keys():
                forecast_list.append(j[i])

            forecast_temp_list = self.forecast_temp_re.findall(r.text)

            self.get_current_conditions(s)
            self.get_hourly_forecast(s)
            self.get_daily_forecast(s, forecast_list, forecast_temp_list)

            self.s = s
        
        except:
            print('Error while trying to fetch forecast')

    def get_current_conditions(self, s):

        #dia, temperatura
        current_conditions = s.find(class_='container cc')
        current_temp = self.digit_re.findall(current_conditions.find(class_='currentTemp').text)[0]

        # sensacao termica, vento, rajada, precipitacao
        other_current_conditions = s.find(class_='info-gradient collapse in acci').find_all('span')
        current_fell_like = self.digit_re.findall(other_current_conditions[1].text.strip())[0]
        current_precipitation = self.digit_re.findall(other_current_conditions[3].text.strip())[0]
        wind = other_current_conditions[5].text.strip()
        current_wind_bearing = self.direction_re.findall(wind)[0]
        current_wind_speed = self.digit_re.findall(wind)[0]
        current_wind_gust = self.digit_re.findall(other_current_conditions[7].text.strip())[0]

        self.data['current'] = { 'temperature': current_temp,
                                 'feels_like': current_fell_like,
                                 'precipitation': current_precipitation,
                                 'wind_bearing': current_wind_bearing,
                                 'wind_speed': current_wind_speed,
                                 'wind_gust': current_wind_gust }

    def get_hourly_forecast(self, s):

        hourly_forecast = [ ]
        hourly_info = [ ]

        today = s.find(class_='table-hourly tab-pane active')
        today_timestamp = int(self.digit_re.findall(today.attrs['id'])[0]) + self.tz_fix

        hourly_extra = today.find_all(class_='collapse ah-body')
        index = 0 
        for hour in today.find_all(class_='ah-header'):
            hourly_info.append([ hour, hourly_extra[index]])
            index += 1

        tomorrow = s.find(class_='table-hourly tab-pane')
        hourly_extra = tomorrow.find_all(class_='collapse ah-body')
        index = 0
        for hour in tomorrow.find_all(class_='ah-header'):
            hourly_info.append([ hour, hourly_extra[index]])
            index += 1

        timestamp = today_timestamp + int(self.digit_re.findall(hourly_info[0][0].find(class_='ah-time').text)[0]) * 3600
        
        for i in hourly_info:
            tmp = i[0].find(class_='ah-temp')
            temperature = self.digit_re.findall(tmp.text.strip())[0]
            icon = i[0].find('i').attrs['class'][1]
            condition = i[0].find('i').attrs['title'].strip()
            precipitation = self.digit_re.findall(i[0].find(class_='ah-prec').text)[0]
            wind = i[0].find(class_='ah-wind').text
            wind_bearing = self.direction_re.findall(wind)[0]
            wind_speed = self.digit_re.findall(wind)[0]  
            extra_val = i[1].find_all(class_="val")
            feels_like = self.digit_re.findall(extra_val[0].text.strip())[0]
            humidity = self.digit_re.findall(extra_val[1].text.strip())[0]
            chance_rain = self.digit_re.findall(extra_val[2].text.strip())[0]
            wind_gust = self.digit_re.findall(extra_val[3].text.strip())[0]
            pressure = self.digit_re.findall(extra_val[4].text.strip())[0]
            uv_index = (self.digit_re.findall(extra_val[5].text.strip()) or [None])[0]
            visibility = (self.digit_re.findall(extra_val[6].text.strip()) or [None])[0]

            hourly_forecast.append( { 'timestamp': timestamp, 'temperature': temperature, 'icon': icon, 
                                      'condition': condition, 'precipitation': precipitation, 'wind_bearing': wind_bearing, 
                                      'wind_speed': wind_speed, 'feels_like': feels_like, 'humidity': humidity, 
                                      'chance_of_rain': chance_rain, 'wind_gust': wind_gust, 'pressure': pressure,
                                      'uv_index': uv_index, 'visibility': visibility})    
            #print('{} {} {} {} {} {} {}'.format(time, temperature, icon, condition, precipitation, wind_bearing, wind_speed))

            timestamp += 3600

        self.data['hourly'] = hourly_forecast

    def get_daily_forecast(self, s, forecast_list, forecast_temp_list):
        
        daily_info = [ ]
        daily_forecast = [ ]
        # today
        daily_info.append(s.find(class_='tab-pane active daily_infos-wrapper'))

        # next 14 days
        for nextday in s.find_all(class_='tab-pane daily_infos-wrapper'):
            daily_info.append(nextday)

        x = 0

        for day in daily_info:
            timestamp = int(day.attrs['id']) + 10800
            precipitation = self.digit_re.findall(day.find_all(class_='val')[1].text.strip())[0]
            chance_rain = self.digit_re.findall(day.find_all(class_='val')[2].text.strip())[0]
            wind = day.find_all(class_='val')[3].text.strip()
            wind_bearing = self.direction_re.findall(wind)[0]
            wind_speed = self.digit_re.findall(wind)[0]
            condition = self.forecast_cond_re.search(forecast_list[x]).groups()[0]
            icon = self.forecast_icon_re.search(forecast_list[x]).groups()[0]
            max_temp = forecast_temp_list[0].split(",")[x]
            min_temp = forecast_temp_list[1].split(",")[x]
            x += 1

            daily_forecast.append( { 'timestamp': timestamp, 'condition': condition, 'icon': icon, 'max_temp': max_temp, 
                                     'min_temp': min_temp, 'precipitation': precipitation, 'chance_of_rain': chance_rain, 
                                     'wind_bearing': wind_bearing, 'wind_speed': wind_speed } )

        self.data['daily'] = daily_forecast

if __name__ == '__main__':
    sm = PySimepar(4106902)
    sm.update()

    print("current conditions:")
    for i in sm.data['current'].keys():
        print('{}: {}'.format(i, sm.data['current'][i]))

    print("hourly forecast")
    for i in sm.data['hourly']:
        print(i)

    print("daily forecast")
    for day in sm.data['daily']:
        print(day)
