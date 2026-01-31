import json
import requests
import sys
import time
import os
from datetime import date
from mridu_manda import setup_mridumanda
from mridu_manda import setup_weather_data



city_weather = None
weather = None
temperature = None
feels_like = None
humidity = None



def main():
    setup_mridumanda.setup()
    setup_weather_data.setup()
    
    if (len(sys.argv) > 1) and (sys.argv[1] == "-m"):
        manual_city() 
    else:
        auto_city()
    
    
def auto_city():
    setup_mridumanda.setup()
    setup_weather_data.setup()
    
    print("Welcome to MriduManda")
    print("Fetching city...")
    city = get_city()
    path_to_api = os.path.join(os.path.expanduser("~"), ".mridumanda", "api.txt")
    api = None
    
    with open (path_to_api, "r") as file:
        line = file.readline()
        
        if ":" in line:
            key, value = line.strip().split(":", 1)
            api = value
    
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api}&units=metric"
    response = requests.get(url)
    
    time.sleep(1)
    os.system('clear')
    
    if response.status_code == 200:
        access_weather(response.json(), city)
        
    else:
        print("Error:", response.status_code)
    
    weather_choice()


def manual_city():
    setup_mridumanda.setup()
    
    print("Welcome to MriduManda")
    
    city = input("Enter a city: ")
    path_to_api = os.path.join(os.path.expanduser("~"), ".mridumanda", "api.txt")
    api = None
    
    with open (path_to_api, "r") as file:
        line = file.readline()
        
        if ":" in line:
            key, value = line.strip().split(":", 1)
            api = value
    
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api}&units=metric"
    response = requests.get(url)
    
    time.sleep(1)
    os.system('clear')
    
    if response.status_code == 200:
        access_weather(response.json(), city)
        
    else:
        print("Error:", response.status_code)
    
    
    weather_choice()


def access_weather(weather_data, city):
    global city_weather, weather, temperature, feels_like, humidity
    
    city_weather = city
    weather = weather_data['weather'][0]['description'].title()
    temperature = weather_data['main']['temp']
    feels_like = weather_data['main']['feels_like']
    humidity = weather_data['main']['humidity']
    
      
def get_city():
    ipinfo_data = requests.get("https://www.ipinfo.io/json")
    city = ipinfo_data.json().get('city')
    
    return city


def weather_choice():
    weather_style = input("Enter option (default / one liner): ")
    
    if weather_style.lower() == "o":
        print_weather_one_line()
    else:
        print_weather()


def print_weather():
    print(f"City \t\t : {str.capitalize(city_weather)}")
    print(f"Weather \t : {weather}")
    print(f"Temperature \t : {temperature}°C")
    print(f"Feels like \t : {feels_like}°C")
    print(f"Humidity \t : {humidity}")
    
    save_weather()


def print_weather_one_line():
    print(f"City: {str.capitalize(city_weather)}   |   Weather: {weather}   |   Temperature: {temperature}°C")
    
    save_weather()


def save_weather():    
    
    setup_weather_data.setup()
    
    weather_report = {"city": str.capitalize(city_weather), "weather_condition": weather, "temperature": temperature, "feels_like": feels_like, "humidity": humidity}
    
    with open(os.path.join(os.path.expanduser("~"), ".mridumanda", "weather.json"), "r+") as file:
        temp_json = json.load(file)
        temp_json[str(date.today())] = weather_report
        file.seek(0)
        json.dump(temp_json, file, indent=4)