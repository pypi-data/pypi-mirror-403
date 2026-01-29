# TRandom

TRandom - A powerful Python package that generates fake data for testing, development, and data anonymization.

## Overview

TRandom is a comprehensive fake data generator based on the popular Faker library, rebranded and customized for TactLabs. It provides an easy-to-use interface for generating realistic fake data across multiple categories including personal information, addresses, companies, internet data, dates, and much more.

## Installation

```bash
pip install tactrandom
```

Or install from source:

```bash
git clone https://github.com/tactlabs/tact-random
cd tact-random
pip install -e .
```

## Quick Start

```python
from trandom import TRandom

# Initialize TRandom
rand = TRandom()

# Generate fake data
print(rand.name())          # 'John Doe'
print(rand.email())         # 'john.doe@example.com'
print(rand.address())       # '123 Main St, Springfield, IL 62701'
print(rand.phone_number())  # '(555) 123-4567'
print(rand.company())       # 'Acme Corporation'
print(rand.animal())        # 'Lion'
print(rand.dog_breed())     # 'Labrador Retriever'
print(rand.music_genre())   # 'Rock'
print(rand.song_title())    # 'Dancing in the Moonlight'
print(rand.sport())         # 'Basketball'
print(rand.team_name())     # 'Chicago Bulls'
print(rand.food())          # 'Pizza'
print(rand.dish())          # 'Grilled Salmon with Asparagus'
print(rand.book_title())    # 'The Shadow of Time'
print(rand.author_name())   # 'Jane Smith'
print(rand.vehicle_make_model()) # 'Toyota Camry'
print(rand.license_plate()) # 'ABC-1234'
print(rand.weather())       # 'Sunny'
print(rand.temperature())   # '72°F'
```

## Features

### Personal Information
- Names (first, last, full)
- Email addresses
- Phone numbers
- Social Security Numbers
- Job titles

### Address Information
- Full addresses
- Cities, states, countries
- Zip codes
- Coordinates (latitude/longitude)

### Company Information
- Company names
- Business emails
- Catch phrases
- Business jargon

### Internet & Technology
- Usernames and passwords
- IP addresses (IPv4, IPv6)
- MAC addresses
- URLs and domains
- User agents

### Dates & Times
- Random dates
- Past and future dates
- Times and timestamps
- Date ranges

### Financial
- Credit card numbers
- Credit card providers
- Currency codes
- IBAN numbers

### Text & Lorem Ipsum
- Words, sentences, paragraphs
- Text of various lengths

### Colors
- Color names
- Hex colors
- RGB colors

### Animals (New!)
- Random animals from all categories
- Mammals, birds, reptiles, amphibians, fish
- Invertebrates
- Domestic and wild animals
- Endangered species
- Dog and cat breeds

### Music (New!)
- Music genres and instruments
- Song titles and album names
- Artist and band names
- Record labels and formats
- Streaming platforms
- Concert venues and awards
- Musical terms and keys
- BPM, duration, and track info
- Playlist names

### Sports (New!)
- All major sports (team and individual)
- Olympic sports
- Team names and athlete names
- Sport positions and equipment
- Venues and famous stadiums
- Leagues and competitions
- Awards and honors
- Scores, rankings, and records
- Jersey numbers and seasons

### Food (New!)
- Fruits, vegetables, meats, and seafood
- Dairy products and grains
- Spices, herbs, and ingredients
- Desserts and beverages
- Cuisines and cooking methods
- Dishes and recipes
- Restaurant types and meal types
- Dietary preferences and taste profiles
- Food prices and nutrition info

### Books & Literature (New!)
- Book titles and author names
- Literary genres and publishers
- Book series and chapter titles
- Book formats and editions
- ISBN numbers and publication years
- Literary awards and reading levels
- Book ratings and reviews
- Bookstore types and book clubs
- Literary terms and languages

### Vehicles & Automotive (New!)
- Vehicle types and manufacturers
- Car makes and models
- Vehicle years and colors
- Fuel types and transmissions
- Engine sizes and drive types
- Vehicle features and specifications
- License plates and VIN numbers
- Mileage and pricing
- Dealerships and insurance

### Weather & Climate (New!)
- Weather conditions and descriptions
- Temperature (Fahrenheit and Celsius)
- Wind speed and direction
- Humidity and precipitation
- Cloud cover and visibility
- Atmospheric pressure
- UV index and air quality
- Weather alerts and seasons
- Moon phases and sunrise/sunset times

## Advanced Usage

### Using Locales

TRandom supports multiple locales for generating localized data:

```python
from trandom import TRandom

# French locale
rand_fr = TRandom('fr_FR')
print(rand_fr.name())      # 'Jean Dupont'
print(rand_fr.address())   # French address

# Spanish locale
rand_es = TRandom('es_ES')
print(rand_es.name())      # 'María García'

# Multiple locales
rand_multi = TRandom(['en_US', 'fr_FR', 'es_ES'])
print(rand_multi.name())   # Randomly picks from any locale
```

### Seeding for Reproducibility

```python
from trandom import TRandom

# Set seed for reproducible results
TRandom.seed(12345)
rand = TRandom()
print(rand.name())  # Always generates the same name

# Reset seed
TRandom.seed(12345)
rand2 = TRandom()
print(rand2.name())  # Same as above
```

### Unique Values

```python
from trandom import TRandom

rand = TRandom()

# Generate unique emails
for _ in range(5):
    print(rand.unique.email())

# Clear unique cache
rand.unique.clear()
```

### Optional Values

```python
from trandom import TRandom

rand = TRandom()

# 50% chance of returning None
print(rand.optional.name())

# 80% chance of returning a value
print(rand.optional.email(prob=0.8))
```

## Examples

See `example.py` for comprehensive usage examples:

```bash
python example.py
```

## API Reference

### Common Methods

- `name()` - Full name
- `first_name()` - First name
- `last_name()` - Last name
- `email()` - Email address
- `phone_number()` - Phone number
- `address()` - Full address
- `city()` - City name
- `state()` - State name
- `country()` - Country name
- `zipcode()` - Zip code
- `company()` - Company name
- `job()` - Job title
- `text()` - Random text
- `date()` - Random date
- `time()` - Random time
- `url()` - Random URL
- `ipv4()` - IPv4 address
- `credit_card_number()` - Credit card number
- `random_int(min, max)` - Random integer
- `pybool()` - Random boolean
- `color_name()` - Color name
- `hex_color()` - Hex color code
- `animal()` - Random animal
- `mammal()` - Random mammal
- `bird()` - Random bird
- `fish()` - Random fish
- `dog_breed()` - Random dog breed
- `cat_breed()` - Random cat breed
- `music_genre()` - Random music genre
- `instrument()` - Random instrument
- `song_title()` - Random song title
- `artist_name()` - Random artist name
- `album_name()` - Random album name
- `sport()` - Random sport
- `team_sport()` - Random team sport
- `individual_sport()` - Random individual sport
- `olympic_sport()` - Random Olympic sport
- `team_name()` - Random team name
- `athlete_name()` - Random athlete name
- `sport_position()` - Random sport position
- `sport_equipment()` - Random sport equipment
- `famous_sport_venue()` - Famous sport venue
- `sport_league()` - Random sport league
- `sport_award()` - Random sport award
- `jersey_number()` - Random jersey number
- `season_year()` - Season year format
- `score()` - Random score
- `record()` - Win-loss record
- `ranking()` - Ranking position
- `food()` - Random food item
- `fruit()` - Random fruit
- `vegetable()` - Random vegetable
- `meat()` - Random meat
- `seafood_item()` - Random seafood
- `dairy_product()` - Random dairy product
- `grain()` - Random grain
- `spice()` - Random spice or herb
- `dessert()` - Random dessert
- `beverage()` - Random beverage
- `cuisine()` - Random cuisine type
- `cooking_method()` - Random cooking method
- `meal_type()` - Random meal type
- `dish()` - Random dish name
- `ingredient()` - Random ingredient
- `restaurant_type()` - Random restaurant type
- `dietary_preference()` - Random dietary preference
- `recipe_name()` - Random recipe name
- `food_price()` - Random food price
- `calories()` - Random calorie count
- `serving_size()` - Random serving size
- `book_title()` - Random book title
- `author_name()` - Random author name
- `literary_genre()` - Random literary genre
- `publisher()` - Random publisher
- `book_format()` - Random book format
- `book_series()` - Random book series
- `chapter_title()` - Random chapter title
- `literary_award()` - Random literary award
- `reading_level()` - Random reading level
- `book_condition()` - Random book condition
- `bookstore_type()` - Random bookstore type
- `publication_year()` - Random publication year
- `page_count()` - Random page count
- `isbn()` - Random ISBN number
- `book_rating()` - Random book rating
- `review_count()` - Random review count
- `edition()` - Random book edition
- `language()` - Random language
- `vehicle()` - Random vehicle type
- `vehicle_type()` - Random vehicle type
- `car_make()` - Random car manufacturer
- `car_model()` - Random car model
- `vehicle_make_model()` - Random make and model
- `vehicle_year()` - Random vehicle year
- `vehicle_color()` - Random vehicle color
- `fuel_type()` - Random fuel type
- `transmission()` - Random transmission type
- `engine_size()` - Random engine size
- `drive_type()` - Random drive type
- `vehicle_feature()` - Random vehicle feature
- `license_plate()` - Random license plate
- `vin()` - Random VIN number
- `vehicle_condition()` - Random vehicle condition
- `mileage()` - Random mileage
- `vehicle_price()` - Random vehicle price
- `dealership_type()` - Random dealership type
- `insurance_type()` - Random insurance type
- `mpg()` - Random MPG
- `horsepower()` - Random horsepower
- `seating_capacity()` - Random seating capacity
- `weather()` - Random weather condition
- `weather_description()` - Detailed weather description
- `temperature()` - Random temperature
- `temperature_celsius()` - Temperature in Celsius
- `temperature_fahrenheit()` - Temperature in Fahrenheit
- `wind_speed()` - Random wind speed
- `wind_direction()` - Random wind direction
- `humidity()` - Random humidity percentage
- `precipitation()` - Random precipitation type
- `precipitation_amount()` - Random precipitation amount
- `cloud_cover()` - Random cloud cover level
- `visibility()` - Random visibility distance
- `pressure()` - Random atmospheric pressure
- `uv_index()` - Random UV index
- `uv_index_level()` - UV index level description
- `air_quality()` - Random air quality level
- `air_quality_index()` - Random AQI
- `weather_alert()` - Random weather alert
- `season()` - Random season
- `moon_phase()` - Random moon phase
- `sunrise_time()` - Random sunrise time
- `sunset_time()` - Random sunset time
- `feels_like_temperature()` - Feels like temperature
- `dew_point()` - Random dew point
- `chance_of_rain()` - Chance of rain percentage

## Requirements

- Python >= 3.10
- numpy
- pandas

## License

MIT License - see LICENSE file for details

## Credits

TRandom is based on the excellent [Faker](https://github.com/joke2k/faker) library by joke2k and contributors. We are grateful for their work in creating such a comprehensive and well-maintained fake data generation library.

**Original Faker Library:**
- Repository: https://github.com/joke2k/faker
- Author: joke2k
- License: MIT

TRandom has been customized and rebranded for TactLabs with additional features and modifications while maintaining the core functionality and spirit of the original Faker library.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues and questions, please open an issue on GitHub:
https://github.com/tactlabs/tact-random/issues
