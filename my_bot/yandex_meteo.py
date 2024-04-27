# temperature,Значение температуры в тени на высоте двух метров над земной поверхностью.
# pressure,Текущее атмосферное давление
# cloudiness,Текущее значение облачности.CLEAR – ясно, до OVERCAST – пасмурно.
# precProbability,Текущая вероятность осадков.[0, 1]
# windSpeed, Скорость ветра на высоте 10 метров над земной поверхностью. m/s
import asyncio
import json

from geopy.geocoders import Nominatim
import aiohttp

from config_reader import settings

geolocator = Nominatim(user_agent="telegram_bot")


async def handle_location():
    city_name = settings.CITY
    location = geolocator.geocode(city_name)

    if location:
        latitude = location.latitude
        longitude = location.longitude
        query_current = """{
          weatherByPoint(request: { lat: %s, lon: %s }) {
            now {
              temperature,
              pressure,
              cloudiness,
              precProbability,
              windSpeed,
            }
          }
        }""" % (latitude, longitude)
        query_tomorrow = """{
                  weatherByPoint(request: { lat: %s, lon: %s }) {
                  forecast {
                    days(limit: 1) {
                    summary {
                      day {
                            temperature,
                            pressure,
                            cloudiness,
                            precProbability,
                            windSpeed,
                          }
                       }                   
                    }
                  }
                 } 
                }""" % (latitude, longitude)
        return query_current, query_tomorrow
    else:
        print("City not found")
        return None


async def async_request(query):
    headers = {"X-Yandex-Weather-Key": settings.YANDEX_TOKEN.get_secret_value()}
    async with aiohttp.ClientSession() as session:
        async with session.post(
                url=str(settings.YANDEXMETEO_URL),
                headers=headers,
                json={"query": query}
        ) as response:
            data = json.loads((await response.read()))
    if data:
        return data

    return None


async def get_weather():
    data_current, data_tomorrow = await handle_location()

    res_current = await async_request(data_current)

    if not res_current:
        return None
    data = res_current['data']['weatherByPoint']['now']

    current_weather_message = (f"Температура: {data['temperature']}°C\n"
                               f"Давление: {data['pressure']} мм.рт.ст.\n"
                               f"Облачность: {'Ясно' if data['cloudiness'] == 'CLEAR' else 'Пасмурно'}\n"
                               f"Осадки: {'Отсутствуют' if data['precProbability'] == 0 else 'Ожидаются'}\n"
                               f"Скорость ветра: {data['windSpeed']} м/c")

    res_tomor = await async_request(data_tomorrow)
    # print(res_current)
    # print(res_tomor)
    if not res_tomor:
        return None

    tomorrow_weather_data = res_tomor['data']['weatherByPoint']['forecast']['days'][0]['summary']['day']
    tomorrow_weather_message = (f"Температура: {tomorrow_weather_data['temperature']}°C\n"
                                f"Давление: {tomorrow_weather_data['pressure']} мм.рт.ст.\n"
                                f"Облачность: {'Ясно' if tomorrow_weather_data['cloudiness'] == 'CLEAR' else 'Пасмурно'}\n"
                                f"Осадки: {'Отсутствуют' if tomorrow_weather_data['precProbability'] == 0 else 'Ожидаются'}\n"
                                f"Скорость ветра: {tomorrow_weather_data['windSpeed']} м/c")

    return current_weather_message, tomorrow_weather_message


asyncio.run(get_weather())
