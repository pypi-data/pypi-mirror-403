from .. import BaseProvider

localized = False


class Provider(BaseProvider):
    """Provider for vehicle and automotive-related data."""

    # Vehicle types
    vehicle_types = [
        "Sedan", "SUV", "Truck", "Coupe", "Convertible", "Hatchback",
        "Wagon", "Minivan", "Van", "Pickup Truck", "Sports Car",
        "Luxury Car", "Compact Car", "Crossover", "Roadster",
        "Limousine", "Bus", "Motorcycle", "Scooter", "ATV",
        "RV", "Camper", "Trailer", "Semi-Truck", "Tow Truck"
    ]

    # Car manufacturers
    car_makes = [
        "Toyota", "Honda", "Ford", "Chevrolet", "Nissan", "BMW", "Mercedes-Benz",
        "Audi", "Volkswagen", "Hyundai", "Kia", "Mazda", "Subaru", "Lexus",
        "Jeep", "Ram", "GMC", "Dodge", "Chrysler", "Buick", "Cadillac",
        "Tesla", "Volvo", "Porsche", "Jaguar", "Land Rover", "Ferrari",
        "Lamborghini", "Maserati", "Bentley", "Rolls-Royce", "Aston Martin",
        "McLaren", "Bugatti", "Alfa Romeo", "Fiat", "Peugeot", "Renault",
        "Citroën", "Mini", "Mitsubishi", "Infiniti", "Acura", "Genesis"
    ]

    # Popular car models by make
    car_models = {
        "Toyota": ["Camry", "Corolla", "RAV4", "Highlander", "Tacoma", "Tundra", "Prius", "4Runner"],
        "Honda": ["Civic", "Accord", "CR-V", "Pilot", "Odyssey", "Fit", "HR-V", "Ridgeline"],
        "Ford": ["F-150", "Mustang", "Explorer", "Escape", "Edge", "Fusion", "Ranger", "Bronco"],
        "Chevrolet": ["Silverado", "Equinox", "Malibu", "Traverse", "Tahoe", "Camaro", "Corvette", "Blazer"],
        "Nissan": ["Altima", "Sentra", "Rogue", "Pathfinder", "Frontier", "Titan", "Maxima", "Murano"],
        "BMW": ["3 Series", "5 Series", "7 Series", "X3", "X5", "X7", "M3", "M5"],
        "Mercedes-Benz": ["C-Class", "E-Class", "S-Class", "GLC", "GLE", "GLS", "A-Class", "CLA"],
        "Audi": ["A3", "A4", "A6", "A8", "Q3", "Q5", "Q7", "Q8"],
        "Tesla": ["Model S", "Model 3", "Model X", "Model Y", "Cybertruck", "Roadster"],
        "default": ["Sedan", "SUV", "Coupe", "Hatchback", "Wagon"]
    }

    # Vehicle colors
    vehicle_colors = [
        "White", "Black", "Silver", "Gray", "Red", "Blue", "Green", "Yellow",
        "Orange", "Brown", "Beige", "Gold", "Purple", "Pink", "Burgundy",
        "Navy Blue", "Dark Green", "Light Blue", "Charcoal", "Pearl White",
        "Metallic Silver", "Midnight Black", "Racing Red", "Electric Blue"
    ]

    # Fuel types
    fuel_types = [
        "Gasoline", "Diesel", "Electric", "Hybrid", "Plug-in Hybrid",
        "Ethanol", "Biodiesel", "Natural Gas", "Propane", "Hydrogen"
    ]

    # Transmission types
    transmission_types = [
        "Automatic", "Manual", "CVT", "Semi-Automatic", "Dual-Clutch",
        "6-Speed Manual", "8-Speed Automatic", "10-Speed Automatic"
    ]

    # Engine sizes
    engine_sizes = [
        "1.5L", "1.6L", "1.8L", "2.0L", "2.4L", "2.5L", "3.0L", "3.5L",
        "4.0L", "5.0L", "5.7L", "6.2L", "6.4L", "V6", "V8", "V12",
        "Inline-4", "Inline-6", "Flat-4", "Flat-6"
    ]

    # Drive types
    drive_types = [
        "FWD", "RWD", "AWD", "4WD", "Front-Wheel Drive", "Rear-Wheel Drive",
        "All-Wheel Drive", "Four-Wheel Drive"
    ]

    # Vehicle features
    vehicle_features = [
        "Sunroof", "Moonroof", "Leather Seats", "Heated Seats", "Cooled Seats",
        "Navigation System", "Backup Camera", "Blind Spot Monitor",
        "Lane Departure Warning", "Adaptive Cruise Control", "Parking Sensors",
        "Keyless Entry", "Push Button Start", "Remote Start", "Apple CarPlay",
        "Android Auto", "Premium Sound System", "Bluetooth", "USB Ports",
        "Third Row Seating", "Roof Rack", "Tow Package", "Sport Package"
    ]

    # License plate patterns (US style)
    license_plate_patterns = [
        "###-####",
        "###-###",
        "ABC-####",
        "ABC-###",
        "##-ABC-##",
        "ABC-##-##",
    ]

    # VIN pattern (simplified)
    vin_pattern = "1HGBH41JXMN######"

    # Vehicle conditions
    vehicle_conditions = [
        "New", "Excellent", "Very Good", "Good", "Fair", "Poor",
        "Certified Pre-Owned", "Like New", "Salvage", "Rebuilt"
    ]

    # Dealership types
    dealership_types = [
        "New Car Dealership", "Used Car Dealership", "Luxury Dealership",
        "Franchise Dealership", "Independent Dealership", "Online Dealership",
        "Buy Here Pay Here", "Certified Pre-Owned Dealer"
    ]

    # Insurance types
    insurance_types = [
        "Liability", "Collision", "Comprehensive", "Full Coverage",
        "Uninsured Motorist", "Personal Injury Protection", "Gap Insurance",
        "Rental Reimbursement", "Roadside Assistance"
    ]

    def vehicle(self) -> str:
        """
        Generate a random vehicle type.
        
        :example: 'SUV'
        """
        return self.random_element(self.vehicle_types)

    def vehicle_type(self) -> str:
        """
        Generate a random vehicle type (alias for vehicle).
        
        :example: 'Sedan'
        """
        return self.vehicle()

    def car_make(self) -> str:
        """
        Generate a random car manufacturer.
        
        :example: 'Toyota'
        """
        return self.random_element(self.car_makes)

    def car_model(self, make: str = None) -> str:
        """
        Generate a random car model, optionally for a specific make.
        
        :param make: Optional car make to get model for
        :example: 'Camry'
        """
        if make and make in self.car_models:
            return self.random_element(self.car_models[make])
        elif make:
            return self.random_element(self.car_models["default"])
        else:
            # Pick a random make and then a model from it
            random_make = self.random_element(list(self.car_models.keys()))
            if random_make == "default":
                random_make = self.random_element([k for k in self.car_models.keys() if k != "default"])
            return self.random_element(self.car_models[random_make])

    def vehicle_make_model(self) -> str:
        """
        Generate a random vehicle make and model combination.
        
        :example: 'Toyota Camry'
        """
        make = self.car_make()
        model = self.car_model(make)
        return f"{make} {model}"

    def vehicle_year(self, min_year: int = 2000, max_year: int = 2024) -> int:
        """
        Generate a random vehicle year.
        
        :param min_year: Minimum year (default: 2000)
        :param max_year: Maximum year (default: 2024)
        :example: 2020
        """
        return self.random_int(min_year, max_year)

    def vehicle_color(self) -> str:
        """
        Generate a random vehicle color.
        
        :example: 'Silver'
        """
        return self.random_element(self.vehicle_colors)

    def fuel_type(self) -> str:
        """
        Generate a random fuel type.
        
        :example: 'Gasoline'
        """
        return self.random_element(self.fuel_types)

    def transmission(self) -> str:
        """
        Generate a random transmission type.
        
        :example: 'Automatic'
        """
        return self.random_element(self.transmission_types)

    def engine_size(self) -> str:
        """
        Generate a random engine size.
        
        :example: '2.5L'
        """
        return self.random_element(self.engine_sizes)

    def drive_type(self) -> str:
        """
        Generate a random drive type.
        
        :example: 'AWD'
        """
        return self.random_element(self.drive_types)

    def vehicle_feature(self) -> str:
        """
        Generate a random vehicle feature.
        
        :example: 'Sunroof'
        """
        return self.random_element(self.vehicle_features)

    def license_plate(self) -> str:
        """
        Generate a random license plate number.
        
        :example: 'ABC-1234'
        """
        pattern = self.random_element(self.license_plate_patterns)
        result = ""
        
        for char in pattern:
            if char == "#":
                result += str(self.random_int(0, 9))
            elif char == "A" or char == "B" or char == "C":
                result += self.random_element("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
            else:
                result += char
        
        return result

    def vin(self) -> str:
        """
        Generate a random Vehicle Identification Number (VIN).
        
        :example: '1HGBH41JXMN109186'
        """
        result = ""
        
        for char in self.vin_pattern:
            if char == "#":
                result += str(self.random_int(0, 9))
            else:
                result += char
        
        return result

    def vehicle_condition(self) -> str:
        """
        Generate a random vehicle condition.
        
        :example: 'Excellent'
        """
        return self.random_element(self.vehicle_conditions)

    def mileage(self, min_miles: int = 0, max_miles: int = 200000) -> int:
        """
        Generate a random mileage.
        
        :param min_miles: Minimum mileage (default: 0)
        :param max_miles: Maximum mileage (default: 200000)
        :example: 45000
        """
        return self.random_int(min_miles, max_miles)

    def vehicle_price(self, min_price: int = 5000, max_price: int = 100000) -> str:
        """
        Generate a random vehicle price.
        
        :param min_price: Minimum price (default: 5000)
        :param max_price: Maximum price (default: 100000)
        :example: '$25,999'
        """
        price = self.random_int(min_price, max_price)
        return f"${price:,}"

    def dealership_type(self) -> str:
        """
        Generate a random dealership type.
        
        :example: 'New Car Dealership'
        """
        return self.random_element(self.dealership_types)

    def insurance_type(self) -> str:
        """
        Generate a random insurance type.
        
        :example: 'Full Coverage'
        """
        return self.random_element(self.insurance_types)

    def mpg(self, min_mpg: int = 15, max_mpg: int = 50) -> int:
        """
        Generate a random MPG (Miles Per Gallon).
        
        :param min_mpg: Minimum MPG (default: 15)
        :param max_mpg: Maximum MPG (default: 50)
        :example: 28
        """
        return self.random_int(min_mpg, max_mpg)

    def horsepower(self, min_hp: int = 100, max_hp: int = 700) -> int:
        """
        Generate a random horsepower.
        
        :param min_hp: Minimum horsepower (default: 100)
        :param max_hp: Maximum horsepower (default: 700)
        :example: 250
        """
        return self.random_int(min_hp, max_hp)

    def seating_capacity(self, min_seats: int = 2, max_seats: int = 8) -> int:
        """
        Generate a random seating capacity.
        
        :param min_seats: Minimum seats (default: 2)
        :param max_seats: Maximum seats (default: 8)
        :example: 5
        """
        return self.random_int(min_seats, max_seats)
