from .. import BaseProvider

localized = False


class Provider(BaseProvider):
    """Provider for food-related data."""

    # Fruits
    fruits = [
        "Apple", "Banana", "Orange", "Grape", "Strawberry", "Blueberry",
        "Raspberry", "Blackberry", "Mango", "Pineapple", "Watermelon",
        "Cantaloupe", "Honeydew", "Peach", "Pear", "Plum", "Cherry",
        "Apricot", "Kiwi", "Papaya", "Guava", "Passion Fruit", "Dragon Fruit",
        "Lychee", "Pomegranate", "Fig", "Date", "Coconut", "Avocado",
        "Lemon", "Lime", "Grapefruit", "Tangerine", "Clementine"
    ]

    # Vegetables
    vegetables = [
        "Carrot", "Broccoli", "Cauliflower", "Spinach", "Lettuce", "Kale",
        "Cabbage", "Brussels Sprouts", "Asparagus", "Celery", "Cucumber",
        "Zucchini", "Eggplant", "Bell Pepper", "Tomato", "Potato",
        "Sweet Potato", "Onion", "Garlic", "Ginger", "Radish", "Beet",
        "Turnip", "Parsnip", "Pumpkin", "Squash", "Corn", "Peas",
        "Green Beans", "Mushroom", "Artichoke", "Leek", "Chard", "Arugula"
    ]

    # Meats
    meats = [
        "Chicken", "Beef", "Pork", "Lamb", "Turkey", "Duck", "Veal",
        "Venison", "Rabbit", "Goat", "Bison", "Quail", "Pheasant",
        "Bacon", "Sausage", "Ham", "Salami", "Prosciutto", "Pepperoni"
    ]

    # Seafood
    seafood = [
        "Salmon", "Tuna", "Cod", "Halibut", "Trout", "Tilapia", "Mahi Mahi",
        "Swordfish", "Sea Bass", "Snapper", "Mackerel", "Sardine", "Anchovy",
        "Shrimp", "Crab", "Lobster", "Scallop", "Oyster", "Clam", "Mussel",
        "Squid", "Octopus", "Caviar"
    ]

    # Dairy products
    dairy = [
        "Milk", "Cheese", "Butter", "Yogurt", "Cream", "Sour Cream",
        "Cottage Cheese", "Cream Cheese", "Mozzarella", "Cheddar",
        "Parmesan", "Swiss Cheese", "Brie", "Gouda", "Feta", "Blue Cheese",
        "Ricotta", "Provolone", "Ice Cream", "Whipped Cream"
    ]

    # Grains and cereals
    grains = [
        "Rice", "Wheat", "Oats", "Barley", "Quinoa", "Corn", "Rye",
        "Millet", "Buckwheat", "Couscous", "Bulgur", "Farro", "Spelt",
        "Bread", "Pasta", "Noodles", "Cereal", "Granola", "Crackers"
    ]

    # Spices and herbs
    spices = [
        "Salt", "Pepper", "Cinnamon", "Nutmeg", "Ginger", "Garlic Powder",
        "Onion Powder", "Paprika", "Cumin", "Coriander", "Turmeric",
        "Cardamom", "Cloves", "Bay Leaf", "Oregano", "Basil", "Thyme",
        "Rosemary", "Sage", "Parsley", "Cilantro", "Dill", "Mint",
        "Chili Powder", "Cayenne", "Curry Powder", "Saffron", "Vanilla"
    ]

    # Desserts
    desserts = [
        "Cake", "Pie", "Cookie", "Brownie", "Cupcake", "Donut", "Muffin",
        "Ice Cream", "Cheesecake", "Tiramisu", "Pudding", "Mousse",
        "Tart", "Pastry", "Eclair", "Macaron", "Croissant", "Cannoli",
        "Baklava", "Flan", "Creme Brulee", "Panna Cotta", "Gelato",
        "Sorbet", "Cobbler", "Strudel", "Truffle", "Chocolate Bar"
    ]

    # Beverages
    beverages = [
        "Water", "Coffee", "Tea", "Juice", "Milk", "Soda", "Lemonade",
        "Iced Tea", "Hot Chocolate", "Smoothie", "Milkshake", "Beer",
        "Wine", "Champagne", "Cocktail", "Whiskey", "Vodka", "Rum",
        "Gin", "Tequila", "Sake", "Cider", "Energy Drink", "Sports Drink",
        "Coconut Water", "Kombucha", "Espresso", "Cappuccino", "Latte",
        "Mocha", "Americano", "Matcha", "Chai"
    ]

    # Cuisines
    cuisines = [
        "Italian", "Chinese", "Japanese", "Mexican", "Indian", "French",
        "Thai", "Greek", "Spanish", "Korean", "Vietnamese", "Turkish",
        "Lebanese", "Moroccan", "Ethiopian", "Brazilian", "Argentinian",
        "Peruvian", "Caribbean", "Mediterranean", "Middle Eastern",
        "American", "British", "German", "Russian", "Polish", "Irish",
        "Scandinavian", "African", "Fusion"
    ]

    # Cooking methods
    cooking_methods = [
        "Grilled", "Baked", "Fried", "Roasted", "Steamed", "Boiled",
        "Sautéed", "Braised", "Stewed", "Poached", "Broiled", "Smoked",
        "Barbecued", "Pan-Fried", "Deep-Fried", "Stir-Fried", "Blanched",
        "Seared", "Caramelized", "Glazed", "Marinated", "Pickled",
        "Fermented", "Raw", "Slow-Cooked"
    ]

    # Meal types
    meal_types = [
        "Breakfast", "Brunch", "Lunch", "Dinner", "Snack", "Appetizer",
        "Main Course", "Side Dish", "Dessert", "Buffet", "Tapas",
        "Tasting Menu", "Prix Fixe", "À la Carte"
    ]

    # Dish name templates
    dish_templates = [
        "{{cooking_method}} {{ingredient}}",
        "{{ingredient}} {{style}}",
        "{{cuisine}} {{ingredient}}",
        "{{ingredient}} with {{ingredient_2}}",
        "{{ingredient}} and {{ingredient_2}}",
        "{{cooking_method}} {{ingredient}} with {{ingredient_2}}",
        "{{cuisine}} Style {{ingredient}}",
        "{{ingredient}} {{cuisine}} Style",
    ]

    # Dish styles
    dish_styles = [
        "Soup", "Salad", "Sandwich", "Wrap", "Bowl", "Plate", "Platter",
        "Skewer", "Taco", "Burrito", "Pizza", "Burger", "Steak", "Curry",
        "Stir-Fry", "Casserole", "Risotto", "Paella", "Sushi", "Ramen"
    ]

    # Restaurant types
    restaurant_types = [
        "Fine Dining", "Casual Dining", "Fast Food", "Fast Casual", "Café",
        "Bistro", "Brasserie", "Pizzeria", "Steakhouse", "Seafood Restaurant",
        "Sushi Bar", "Ramen Shop", "Taco Stand", "Food Truck", "Diner",
        "Buffet", "Bakery", "Patisserie", "Ice Cream Parlor", "Juice Bar",
        "Coffee Shop", "Tea House", "Wine Bar", "Pub", "Gastropub"
    ]

    # Dietary preferences
    dietary_preferences = [
        "Vegetarian", "Vegan", "Gluten-Free", "Dairy-Free", "Nut-Free",
        "Kosher", "Halal", "Paleo", "Keto", "Low-Carb", "Low-Fat",
        "Sugar-Free", "Organic", "Raw", "Pescatarian"
    ]

    # Taste profiles
    taste_profiles = [
        "Sweet", "Salty", "Sour", "Bitter", "Umami", "Spicy", "Savory",
        "Tangy", "Smoky", "Creamy", "Crispy", "Crunchy", "Tender",
        "Juicy", "Rich", "Light", "Fresh", "Zesty", "Mild", "Bold"
    ]

    def food(self) -> str:
        """
        Generate a random food item from all categories.
        
        :example: 'Pizza'
        """
        all_foods = (
            self.fruits + self.vegetables + self.meats + 
            self.seafood + self.dairy + self.grains
        )
        return self.random_element(all_foods)

    def fruit(self) -> str:
        """
        Generate a random fruit name.
        
        :example: 'Apple'
        """
        return self.random_element(self.fruits)

    def vegetable(self) -> str:
        """
        Generate a random vegetable name.
        
        :example: 'Carrot'
        """
        return self.random_element(self.vegetables)

    def meat(self) -> str:
        """
        Generate a random meat type.
        
        :example: 'Chicken'
        """
        return self.random_element(self.meats)

    def seafood_item(self) -> str:
        """
        Generate a random seafood item.
        
        :example: 'Salmon'
        """
        return self.random_element(self.seafood)

    def dairy_product(self) -> str:
        """
        Generate a random dairy product.
        
        :example: 'Cheese'
        """
        return self.random_element(self.dairy)

    def grain(self) -> str:
        """
        Generate a random grain or cereal.
        
        :example: 'Rice'
        """
        return self.random_element(self.grains)

    def spice(self) -> str:
        """
        Generate a random spice or herb.
        
        :example: 'Cinnamon'
        """
        return self.random_element(self.spices)

    def dessert(self) -> str:
        """
        Generate a random dessert name.
        
        :example: 'Chocolate Cake'
        """
        return self.random_element(self.desserts)

    def beverage(self) -> str:
        """
        Generate a random beverage name.
        
        :example: 'Coffee'
        """
        return self.random_element(self.beverages)

    def cuisine(self) -> str:
        """
        Generate a random cuisine type.
        
        :example: 'Italian'
        """
        return self.random_element(self.cuisines)

    def cooking_method(self) -> str:
        """
        Generate a random cooking method.
        
        :example: 'Grilled'
        """
        return self.random_element(self.cooking_methods)

    def meal_type(self) -> str:
        """
        Generate a random meal type.
        
        :example: 'Breakfast'
        """
        return self.random_element(self.meal_types)

    def dish(self) -> str:
        """
        Generate a random dish name.
        
        :example: 'Grilled Salmon with Asparagus'
        """
        template = self.random_element(self.dish_templates)
        result = template
        
        # Get all ingredients for substitution
        all_ingredients = (
            self.fruits + self.vegetables + self.meats + 
            self.seafood + self.grains
        )
        
        # Replace placeholders
        if "{{cooking_method}}" in result:
            result = result.replace("{{cooking_method}}", self.random_element(self.cooking_methods))
        if "{{ingredient}}" in result:
            result = result.replace("{{ingredient}}", self.random_element(all_ingredients))
        if "{{ingredient_2}}" in result:
            result = result.replace("{{ingredient_2}}", self.random_element(all_ingredients))
        if "{{cuisine}}" in result:
            result = result.replace("{{cuisine}}", self.random_element(self.cuisines))
        if "{{style}}" in result:
            result = result.replace("{{style}}", self.random_element(self.dish_styles))
        
        return result

    def ingredient(self) -> str:
        """
        Generate a random ingredient.
        
        :example: 'Olive Oil'
        """
        all_ingredients = (
            self.fruits + self.vegetables + self.meats + 
            self.seafood + self.dairy + self.grains + self.spices
        )
        return self.random_element(all_ingredients)

    def restaurant_type(self) -> str:
        """
        Generate a random restaurant type.
        
        :example: 'Fine Dining'
        """
        return self.random_element(self.restaurant_types)

    def dietary_preference(self) -> str:
        """
        Generate a random dietary preference.
        
        :example: 'Vegetarian'
        """
        return self.random_element(self.dietary_preferences)

    def taste_profile(self) -> str:
        """
        Generate a random taste profile.
        
        :example: 'Sweet'
        """
        return self.random_element(self.taste_profiles)

    def recipe_name(self) -> str:
        """
        Generate a random recipe name.
        
        :example: 'Grandma's Secret Chocolate Cake'
        """
        templates = [
            "{{adjective}} {{dish}}",
            "{{name}}'s {{dish}}",
            "{{cuisine}} {{dish}}",
            "Homemade {{dish}}",
            "Classic {{dish}}",
            "Traditional {{dish}}",
            "Modern {{dish}}",
        ]
        
        adjectives = ["Secret", "Famous", "Special", "Delicious", "Perfect", 
                     "Ultimate", "Best", "Authentic", "Gourmet", "Rustic"]
        
        template = self.random_element(templates)
        result = template
        
        if "{{adjective}}" in result:
            result = result.replace("{{adjective}}", self.random_element(adjectives))
        if "{{name}}" in result:
            result = self.generator.parse(result)
        if "{{dish}}" in result:
            result = result.replace("{{dish}}", self.dessert() if self.random_int(0, 1) else self.random_element(self.dish_styles))
        if "{{cuisine}}" in result:
            result = result.replace("{{cuisine}}", self.random_element(self.cuisines))
        
        return result

    def food_price(self, min_price: float = 5.0, max_price: float = 50.0) -> str:
        """
        Generate a random food price.
        
        :param min_price: Minimum price (default: 5.0)
        :param max_price: Maximum price (default: 50.0)
        :example: '$12.99'
        """
        price = self.random_int(int(min_price * 100), int(max_price * 100)) / 100
        return f"${price:.2f}"

    def calories(self, min_cal: int = 100, max_cal: int = 1000) -> int:
        """
        Generate random calorie count.
        
        :param min_cal: Minimum calories (default: 100)
        :param max_cal: Maximum calories (default: 1000)
        :example: 450
        """
        return self.random_int(min_cal, max_cal)

    def serving_size(self) -> str:
        """
        Generate a random serving size.
        
        :example: '2 cups'
        """
        amounts = ["1/4", "1/2", "3/4", "1", "2", "3", "4", "6", "8"]
        units = ["cup", "cups", "tablespoon", "tablespoons", "teaspoon", 
                "teaspoons", "oz", "lb", "g", "kg", "ml", "L", "piece", "pieces"]
        
        amount = self.random_element(amounts)
        unit = self.random_element(units)
        
        return f"{amount} {unit}"
