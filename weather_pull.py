import requests
import pandas as pd
import streamlit as st

def check_weather():
    URL = f'https://api.weather.gov/gridpoints/IND/59,70/forecast/hourly'

    response = requests.get(URL)
    forecast = response.json()['properties']
    #%%
    periods = forecast['periods']
    df = pd.DataFrame(periods)
    df.loc[:,'probabilityOfPrecipitation'] = [i['value'] for i in df.loc[:,'probabilityOfPrecipitation']]
    # %%
    # Get the current date with timezone as 'US/Eastern' and add 1 day
    time_cut = pd.Timestamp.now(tz='US/Eastern').normalize() + pd.Timedelta(days=2)
    date_tomorrow = pd.Timestamp.now(tz='US/Eastern').normalize() + pd.Timedelta(hours=24)

    # Ensure 'startTime' is in datetime format
    df['startTime'] = pd.to_datetime(df['startTime'])

    # Check if 'startTime' is naive (no timezone) and localize if necessary
    if df['startTime'].dt.tz is None:
        df['startTime'] = df['startTime'].dt.tz_localize('US/Eastern')
    else:
        df['startTime'] = df['startTime'].dt.tz_convert('US/Eastern')

    # Filter rows where 'startTime' is less than 'time_cut'
    df = df[df['startTime'] < time_cut]
    # %% Break into sub datasets
    df_tomorrow = df[df['startTime'] >= date_tomorrow]
    df_tomorrow.index = df_tomorrow.startTime
    work = df_tomorrow.between_time('07:00','18:00')
    work_small = df_tomorrow.between_time('09:00','16:00')
    ride = pd.concat([df_tomorrow.between_time('07:00','9:00'),df_tomorrow.between_time('16:00','18:00')])
    nos = []    
    # %% Precip check 1
    max_ride_precip = ride.probabilityOfPrecipitation.max()
    if max_ride_precip >= 20:
        nos.append('No, likely rain during commute')
    #%% Precip check 2
    max_work_precip = work_small.probabilityOfPrecipitation.max()
    average_work_temp = work_small.temperature.mean()
    if max_work_precip > 10 and average_work_temp < 40:
        nos.append('No, can\'t leave battery on')
    #%% Temp check
    min_work_temp = work.temperature.min()
    if min_work_temp < 10:
        nos.append('No, too cold')
    max_work_temp = work.temperature.max()
    if max_work_temp > 100:
        nos.append('No, too hot')
    
    if nos == []:
        nos = ['Yes, ride']
    df = df[['startTime','temperature','probabilityOfPrecipitation','windSpeed','shortForecast','icon']]
    return df, nos

#Initialize on first load
if 'df' not in st.session_state and 'nos' not in st.session_state:
    st.session_state['df'], st.session_state['nos'] = check_weather()

st.write('Last refresh ' + str(st.session_state['df'].startTime.min()))
st.subheader('Can I ride?')
for no in st.session_state['nos']:
    st.write(no)

st.subheader("Current weather Indianapolis")
col1, col2, col3 = st.columns(3)
col1.metric("🌡️ Temperature", f"{st.session_state['df']['temperature'][0]}°F")
col2.metric("💧 Precipitation", f"{st.session_state['df']['probabilityOfPrecipitation'][0]}%")
col3.metric("🌬️ Wind Speed", f"{st.session_state['df']['windSpeed'][0]}")
st.image(st.session_state['df']['icon'][0])

st.subheader('Weather Data - Now through Tomorrow')
st.area_chart(st.session_state['df'], x="startTime", 
             y=['probabilityOfPrecipitation','temperature'],
             color=["#a0a0a0","#000000"],
             stack=False)

#Referesh option
if st.button('Refresh weather'):
    st.session_state['df'], st.session_state['nos'] = check_weather()

st.dataframe(st.session_state['df'])