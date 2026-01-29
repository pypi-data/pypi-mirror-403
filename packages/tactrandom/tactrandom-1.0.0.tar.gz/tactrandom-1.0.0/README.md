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

## Requirements

- Python >= 3.10
- numpy
- pandas

## License

MIT License - see LICENSE file for details

## Credits

Based on the Faker library by joke2k. Customized and maintained by TactLabs.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues and questions, please open an issue on GitHub:
https://github.com/tactlabs/tact-random/issues
