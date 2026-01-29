from .. import BaseProvider

localized = False


class Provider(BaseProvider):
    """Provider for animal-related data."""

    # Mammals
    mammals = [
        "Dog", "Cat", "Lion", "Tiger", "Elephant", "Giraffe", "Zebra", "Horse",
        "Cow", "Pig", "Sheep", "Goat", "Rabbit", "Mouse", "Rat", "Hamster",
        "Guinea Pig", "Squirrel", "Chipmunk", "Beaver", "Otter", "Seal",
        "Walrus", "Whale", "Dolphin", "Porpoise", "Bear", "Panda", "Koala",
        "Kangaroo", "Wallaby", "Opossum", "Raccoon", "Skunk", "Fox", "Wolf",
        "Coyote", "Jackal", "Hyena", "Cheetah", "Leopard", "Jaguar", "Cougar",
        "Lynx", "Bobcat", "Monkey", "Gorilla", "Chimpanzee", "Orangutan",
        "Baboon", "Lemur", "Sloth", "Anteater", "Armadillo", "Hedgehog",
        "Porcupine", "Bat", "Mole", "Shrew", "Deer", "Moose", "Elk", "Caribou",
        "Antelope", "Gazelle", "Buffalo", "Bison", "Yak", "Camel", "Llama",
        "Alpaca", "Rhinoceros", "Hippopotamus", "Tapir", "Aardvark"
    ]

    # Birds
    birds = [
        "Eagle", "Hawk", "Falcon", "Owl", "Parrot", "Macaw", "Cockatoo",
        "Parakeet", "Canary", "Finch", "Sparrow", "Robin", "Blue Jay",
        "Cardinal", "Crow", "Raven", "Magpie", "Starling", "Swallow",
        "Swift", "Hummingbird", "Woodpecker", "Kingfisher", "Pelican",
        "Seagull", "Albatross", "Penguin", "Ostrich", "Emu", "Cassowary",
        "Kiwi", "Peacock", "Pheasant", "Quail", "Turkey", "Chicken",
        "Duck", "Goose", "Swan", "Flamingo", "Heron", "Stork", "Crane",
        "Ibis", "Spoonbill", "Vulture", "Condor", "Kite", "Buzzard"
    ]

    # Reptiles
    reptiles = [
        "Snake", "Python", "Boa", "Cobra", "Viper", "Rattlesnake", "Anaconda",
        "Lizard", "Gecko", "Iguana", "Chameleon", "Monitor Lizard",
        "Komodo Dragon", "Crocodile", "Alligator", "Caiman", "Gharial",
        "Turtle", "Tortoise", "Sea Turtle", "Terrapin", "Snapping Turtle"
    ]

    # Amphibians
    amphibians = [
        "Frog", "Toad", "Tree Frog", "Bullfrog", "Poison Dart Frog",
        "Salamander", "Newt", "Axolotl", "Caecilian"
    ]

    # Fish
    fishes = [
        "Goldfish", "Koi", "Betta", "Guppy", "Tetra", "Angelfish", "Discus",
        "Clownfish", "Tang", "Damselfish", "Wrasse", "Grouper", "Snapper",
        "Bass", "Trout", "Salmon", "Pike", "Catfish", "Carp", "Tuna",
        "Swordfish", "Marlin", "Shark", "Great White Shark", "Hammerhead Shark",
        "Tiger Shark", "Whale Shark", "Ray", "Manta Ray", "Stingray",
        "Eel", "Moray Eel", "Seahorse", "Pufferfish", "Lionfish", "Barracuda"
    ]

    # Invertebrates
    invertebrates = [
        "Butterfly", "Moth", "Bee", "Wasp", "Ant", "Termite", "Beetle",
        "Ladybug", "Firefly", "Dragonfly", "Damselfly", "Grasshopper",
        "Cricket", "Mantis", "Stick Insect", "Cockroach", "Fly", "Mosquito",
        "Spider", "Tarantula", "Scorpion", "Tick", "Mite", "Centipede",
        "Millipede", "Snail", "Slug", "Octopus", "Squid", "Cuttlefish",
        "Nautilus", "Jellyfish", "Coral", "Sea Anemone", "Starfish",
        "Sea Urchin", "Sea Cucumber", "Crab", "Lobster", "Shrimp", "Prawn",
        "Crayfish", "Barnacle", "Clam", "Oyster", "Mussel", "Scallop",
        "Worm", "Earthworm", "Leech"
    ]

    # Domestic animals
    domestic_animals = [
        "Dog", "Cat", "Horse", "Cow", "Pig", "Sheep", "Goat", "Chicken",
        "Duck", "Goose", "Turkey", "Rabbit", "Guinea Pig", "Hamster",
        "Gerbil", "Ferret", "Parrot", "Canary", "Goldfish"
    ]

    # Wild animals
    wild_animals = [
        "Lion", "Tiger", "Bear", "Wolf", "Elephant", "Giraffe", "Zebra",
        "Rhinoceros", "Hippopotamus", "Crocodile", "Alligator", "Shark",
        "Eagle", "Hawk", "Owl", "Snake", "Lizard", "Frog", "Whale", "Dolphin"
    ]

    # Endangered species
    endangered_species_list = [
        "Giant Panda", "Snow Leopard", "Tiger", "Asian Elephant",
        "Black Rhinoceros", "Orangutan", "Gorilla", "Blue Whale",
        "Sea Turtle", "Polar Bear", "Amur Leopard", "Vaquita",
        "Javan Rhinoceros", "Sumatran Elephant", "Hawksbill Turtle",
        "Saola", "Kakapo", "Philippine Eagle", "California Condor"
    ]

    # Dog breeds
    dog_breeds = [
        "Labrador Retriever", "German Shepherd", "Golden Retriever", "Bulldog",
        "Beagle", "Poodle", "Rottweiler", "Yorkshire Terrier", "Boxer",
        "Dachshund", "Siberian Husky", "Great Dane", "Doberman Pinscher",
        "Shih Tzu", "Boston Terrier", "Pomeranian", "Chihuahua", "Pug",
        "Border Collie", "Australian Shepherd", "Cocker Spaniel", "Maltese",
        "Shetland Sheepdog", "Cavalier King Charles Spaniel", "Corgi"
    ]

    # Cat breeds
    cat_breeds = [
        "Persian", "Maine Coon", "Siamese", "Ragdoll", "Bengal", "Abyssinian",
        "Birman", "Oriental Shorthair", "Sphynx", "Devon Rex", "American Shorthair",
        "British Shorthair", "Scottish Fold", "Russian Blue", "Norwegian Forest Cat",
        "Burmese", "Manx", "Himalayan", "Exotic Shorthair", "Turkish Angora"
    ]

    def animal(self) -> str:
        """
        Generate a random animal name from all categories.
        
        :example: 'Lion'
        """
        all_animals = (
            self.mammals + self.birds + self.reptiles + 
            self.amphibians + self.fishes + self.invertebrates
        )
        return self.random_element(all_animals)

    def mammal(self) -> str:
        """
        Generate a random mammal name.
        
        :example: 'Elephant'
        """
        return self.random_element(self.mammals)

    def bird(self) -> str:
        """
        Generate a random bird name.
        
        :example: 'Eagle'
        """
        return self.random_element(self.birds)

    def reptile(self) -> str:
        """
        Generate a random reptile name.
        
        :example: 'Snake'
        """
        return self.random_element(self.reptiles)

    def amphibian(self) -> str:
        """
        Generate a random amphibian name.
        
        :example: 'Frog'
        """
        return self.random_element(self.amphibians)

    def fish(self) -> str:
        """
        Generate a random fish name.
        
        :example: 'Goldfish'
        """
        return self.random_element(self.fishes)

    def invertebrate(self) -> str:
        """
        Generate a random invertebrate name.
        
        :example: 'Butterfly'
        """
        return self.random_element(self.invertebrates)

    def domestic_animal(self) -> str:
        """
        Generate a random domestic animal name.
        
        :example: 'Dog'
        """
        return self.random_element(self.domestic_animals)

    def wild_animal(self) -> str:
        """
        Generate a random wild animal name.
        
        :example: 'Lion'
        """
        return self.random_element(self.wild_animals)

    def endangered_species(self) -> str:
        """
        Generate a random endangered species name.
        
        :example: 'Giant Panda'
        """
        return self.random_element(self.endangered_species_list)

    def dog_breed(self) -> str:
        """
        Generate a random dog breed name.
        
        :example: 'Labrador Retriever'
        """
        return self.random_element(self.dog_breeds)

    def cat_breed(self) -> str:
        """
        Generate a random cat breed name.
        
        :example: 'Persian'
        """
        return self.random_element(self.cat_breeds)

    def animal_type(self) -> str:
        """
        Generate a random animal type/category.
        
        :example: 'Mammal'
        """
        types = ["Mammal", "Bird", "Reptile", "Amphibian", "Fish", "Invertebrate"]
        return self.random_element(types)
