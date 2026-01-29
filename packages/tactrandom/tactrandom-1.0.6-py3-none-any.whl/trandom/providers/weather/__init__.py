from .. import BaseProvider

localized = False


class Provider(BaseProvider):
    """Provider for weather and meteorological data."""

    # Weather conditions
    weather_conditions = [
        "Sunny", "Partly Cloudy", "Cloudy", "Overcast", "Clear",
        "Rainy", "Light Rain", "Heavy Rain", "Drizzle", "Showers",
        "Thunderstorm", "Lightning", "Stormy", "Snowy", "Light Snow",
        "Heavy Snow", "Blizzard", "Sleet", "Freezing Rain", "Hail",
        "Foggy", "Misty", "Hazy", "Windy", "Breezy", "Calm",
        "Hot", "Warm", "Cool", "Cold", "Freezing", "Humid", "Dry"
    ]

    # Detailed weather descriptions
    weather_descriptions = [
        "Clear skies with plenty of sunshine",
        "Partly cloudy with occasional sun",
        "Mostly cloudy throughout the day",
        "Overcast with gray skies",
        "Light rain expected in the afternoon",
        "Heavy rain with possible flooding",
        "Scattered showers throughout the day",
        "Thunderstorms likely in the evening",
        "Light snow flurries expected",
        "Heavy snowfall with accumulation",
        "Foggy conditions reducing visibility",
        "Windy with gusts up to 40 mph",
        "Humid conditions with possible rain",
        "Dry and sunny all day",
        "Partly cloudy with a chance of rain",
        "Clear and cold overnight",
        "Warm and sunny with light breeze",
        "Cool and breezy with clouds",
        "Hot and humid with afternoon storms",
        "Freezing temperatures with ice"
    ]

    # Precipitation types
    precipitation_types = [
        "No Precipitation", "Light Rain", "Moderate Rain", "Heavy Rain",
        "Light Snow", "Moderate Snow", "Heavy Snow", "Sleet",
        "Freezing Rain", "Hail", "Drizzle", "Showers", "Flurries"
    ]

    # Cloud cover levels
    cloud_cover_levels = [
        "Clear", "Mostly Clear", "Partly Cloudy", "Mostly Cloudy",
        "Cloudy", "Overcast"
    ]

    # Wind directions
    wind_directions = [
        "N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
        "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW",
        "North", "Northeast", "East", "Southeast",
        "South", "Southwest", "West", "Northwest"
    ]

    # Air quality levels
    air_quality_levels = [
        "Good", "Moderate", "Unhealthy for Sensitive Groups",
        "Unhealthy", "Very Unhealthy", "Hazardous"
    ]

    # UV index levels
    uv_index_levels = [
        "Low", "Moderate", "High", "Very High", "Extreme"
    ]

    # Weather alerts
    weather_alerts = [
        "No Alerts", "Heat Advisory", "Wind Advisory", "Flood Watch",
        "Flood Warning", "Severe Thunderstorm Watch", "Severe Thunderstorm Warning",
        "Tornado Watch", "Tornado Warning", "Winter Storm Watch",
        "Winter Storm Warning", "Blizzard Warning", "Ice Storm Warning",
        "Hurricane Watch", "Hurricane Warning", "Tropical Storm Watch",
        "Tropical Storm Warning", "High Wind Warning", "Freeze Warning"
    ]

    # Seasons
    seasons = ["Spring", "Summer", "Fall", "Autumn", "Winter"]

    # Moon phases
    moon_phases = [
        "New Moon", "Waxing Crescent", "First Quarter", "Waxing Gibbous",
        "Full Moon", "Waning Gibbous", "Last Quarter", "Waning Crescent"
    ]

    def weather(self) -> str:
        """
        Generate a random weather condition.
        
        :example: 'Sunny'
        """
        return self.random_element(self.weather_conditions)

    def weather_description(self) -> str:
        """
        Generate a random detailed weather description.
        
        :example: 'Clear skies with plenty of sunshine'
        """
        return self.random_element(self.weather_descriptions)

    def temperature(self, min_temp: int = -20, max_temp: int = 110, unit: str = "F") -> str:
        """
        Generate a random temperature.
        
        :param min_temp: Minimum temperature (default: -20)
        :param max_temp: Maximum temperature (default: 110)
        :param unit: Temperature unit 'F' or 'C' (default: 'F')
        :example: '72°F'
        """
        temp = self.random_int(min_temp, max_temp)
        return f"{temp}°{unit}"

    def temperature_celsius(self, min_temp: int = -30, max_temp: int = 45) -> str:
        """
        Generate a random temperature in Celsius.
        
        :param min_temp: Minimum temperature (default: -30)
        :param max_temp: Maximum temperature (default: 45)
        :example: '22°C'
        """
        return self.temperature(min_temp, max_temp, "C")

    def temperature_fahrenheit(self, min_temp: int = -20, max_temp: int = 110) -> str:
        """
        Generate a random temperature in Fahrenheit.
        
        :param min_temp: Minimum temperature (default: -20)
        :param max_temp: Maximum temperature (default: 110)
        :example: '72°F'
        """
        return self.temperature(min_temp, max_temp, "F")

    def wind_speed(self, min_speed: int = 0, max_speed: int = 60, unit: str = "mph") -> str:
        """
        Generate a random wind speed.
        
        :param min_speed: Minimum speed (default: 0)
        :param max_speed: Maximum speed (default: 60)
        :param unit: Speed unit 'mph' or 'kph' (default: 'mph')
        :example: '15 mph'
        """
        speed = self.random_int(min_speed, max_speed)
        return f"{speed} {unit}"

    def wind_direction(self) -> str:
        """
        Generate a random wind direction.
        
        :example: 'NW'
        """
        return self.random_element(self.wind_directions)

    def humidity(self, min_humidity: int = 20, max_humidity: int = 100) -> str:
        """
        Generate a random humidity percentage.
        
        :param min_humidity: Minimum humidity (default: 20)
        :param max_humidity: Maximum humidity (default: 100)
        :example: '65%'
        """
        humidity = self.random_int(min_humidity, max_humidity)
        return f"{humidity}%"

    def precipitation(self) -> str:
        """
        Generate a random precipitation type.
        
        :example: 'Light Rain'
        """
        return self.random_element(self.precipitation_types)

    def precipitation_amount(self, min_amount: float = 0.0, max_amount: float = 5.0, unit: str = "in") -> str:
        """
        Generate a random precipitation amount.
        
        :param min_amount: Minimum amount (default: 0.0)
        :param max_amount: Maximum amount (default: 5.0)
        :param unit: Unit 'in' or 'mm' (default: 'in')
        :example: '0.5 in'
        """
        amount = self.random_int(int(min_amount * 10), int(max_amount * 10)) / 10
        return f"{amount} {unit}"

    def cloud_cover(self) -> str:
        """
        Generate a random cloud cover level.
        
        :example: 'Partly Cloudy'
        """
        return self.random_element(self.cloud_cover_levels)

    def visibility(self, min_miles: int = 0, max_miles: int = 10, unit: str = "miles") -> str:
        """
        Generate a random visibility distance.
        
        :param min_miles: Minimum visibility (default: 0)
        :param max_miles: Maximum visibility (default: 10)
        :param unit: Unit 'miles' or 'km' (default: 'miles')
        :example: '10 miles'
        """
        distance = self.random_int(min_miles, max_miles)
        return f"{distance} {unit}"

    def pressure(self, min_pressure: int = 28, max_pressure: int = 31, unit: str = "inHg") -> str:
        """
        Generate a random atmospheric pressure.
        
        :param min_pressure: Minimum pressure (default: 28)
        :param max_pressure: Maximum pressure (default: 31)
        :param unit: Unit 'inHg' or 'mb' (default: 'inHg')
        :example: '29.92 inHg'
        """
        if unit == "inHg":
            pressure = self.random_int(min_pressure * 100, max_pressure * 100) / 100
            return f"{pressure:.2f} {unit}"
        else:  # mb or hPa
            pressure = self.random_int(950, 1050)
            return f"{pressure} {unit}"

    def uv_index(self, min_index: int = 0, max_index: int = 11) -> int:
        """
        Generate a random UV index.
        
        :param min_index: Minimum UV index (default: 0)
        :param max_index: Maximum UV index (default: 11)
        :example: 7
        """
        return self.random_int(min_index, max_index)

    def uv_index_level(self) -> str:
        """
        Generate a random UV index level description.
        
        :example: 'High'
        """
        return self.random_element(self.uv_index_levels)

    def air_quality(self) -> str:
        """
        Generate a random air quality level.
        
        :example: 'Good'
        """
        return self.random_element(self.air_quality_levels)

    def air_quality_index(self, min_aqi: int = 0, max_aqi: int = 300) -> int:
        """
        Generate a random Air Quality Index (AQI).
        
        :param min_aqi: Minimum AQI (default: 0)
        :param max_aqi: Maximum AQI (default: 300)
        :example: 45
        """
        return self.random_int(min_aqi, max_aqi)

    def weather_alert(self) -> str:
        """
        Generate a random weather alert.
        
        :example: 'Severe Thunderstorm Watch'
        """
        return self.random_element(self.weather_alerts)

    def season(self) -> str:
        """
        Generate a random season.
        
        :example: 'Summer'
        """
        return self.random_element(self.seasons)

    def moon_phase(self) -> str:
        """
        Generate a random moon phase.
        
        :example: 'Full Moon'
        """
        return self.random_element(self.moon_phases)

    def sunrise_time(self) -> str:
        """
        Generate a random sunrise time.
        
        :example: '6:45 AM'
        """
        hour = self.random_int(5, 7)
        minute = self.random_int(0, 59)
        return f"{hour}:{minute:02d} AM"

    def sunset_time(self) -> str:
        """
        Generate a random sunset time.
        
        :example: '7:30 PM'
        """
        hour = self.random_int(5, 9)
        minute = self.random_int(0, 59)
        return f"{hour}:{minute:02d} PM"

    def feels_like_temperature(self, min_temp: int = -20, max_temp: int = 110, unit: str = "F") -> str:
        """
        Generate a random 'feels like' temperature.
        
        :param min_temp: Minimum temperature (default: -20)
        :param max_temp: Maximum temperature (default: 110)
        :param unit: Temperature unit 'F' or 'C' (default: 'F')
        :example: '68°F'
        """
        return self.temperature(min_temp, max_temp, unit)

    def dew_point(self, min_temp: int = -20, max_temp: int = 80, unit: str = "F") -> str:
        """
        Generate a random dew point temperature.
        
        :param min_temp: Minimum temperature (default: -20)
        :param max_temp: Maximum temperature (default: 80)
        :param unit: Temperature unit 'F' or 'C' (default: 'F')
        :example: '55°F'
        """
        return self.temperature(min_temp, max_temp, unit)

    def chance_of_rain(self, min_chance: int = 0, max_chance: int = 100) -> str:
        """
        Generate a random chance of rain percentage.
        
        :param min_chance: Minimum chance (default: 0)
        :param max_chance: Maximum chance (default: 100)
        :example: '30%'
        """
        chance = self.random_int(min_chance, max_chance)
        return f"{chance}%"
