from .. import BaseProvider

localized = False


class Provider(BaseProvider):
    """Provider for book and literature-related data."""

    # Literary genres
    literary_genres = [
        "Fiction", "Non-Fiction", "Mystery", "Thriller", "Romance",
        "Science Fiction", "Fantasy", "Horror", "Historical Fiction",
        "Literary Fiction", "Contemporary Fiction", "Young Adult",
        "Children's Literature", "Biography", "Autobiography", "Memoir",
        "Self-Help", "Business", "History", "Philosophy", "Psychology",
        "Science", "Travel", "Cooking", "Art", "Poetry", "Drama",
        "Crime", "Detective", "Adventure", "Western", "Dystopian",
        "Paranormal", "Urban Fantasy", "Epic Fantasy", "Space Opera",
        "Cyberpunk", "Steampunk", "Magical Realism", "Satire", "Humor"
    ]

    # Publishers
    publishers = [
        "Penguin Random House", "HarperCollins", "Simon & Schuster",
        "Hachette Book Group", "Macmillan Publishers", "Scholastic",
        "Pearson", "Wiley", "Oxford University Press", "Cambridge University Press",
        "Bloomsbury", "Vintage Books", "Knopf", "Crown Publishing",
        "Little, Brown and Company", "Doubleday", "Viking Press",
        "Farrar, Straus and Giroux", "Grove Press", "New Directions",
        "Tor Books", "Del Rey Books", "Ace Books", "DAW Books",
        "Orbit Books", "Baen Books", "Harlequin", "Kensington Publishing"
    ]

    # Book formats
    book_formats = [
        "Hardcover", "Paperback", "Mass Market Paperback", "eBook",
        "Audiobook", "Kindle Edition", "Large Print", "Board Book",
        "Leather Bound", "Box Set", "Collector's Edition"
    ]

    # Book series templates
    series_templates = [
        "The {{word}} Chronicles",
        "The {{word}} Saga",
        "The {{word}} Trilogy",
        "{{word}} Series",
        "The {{word}} Cycle",
        "Tales of {{word}}",
        "The {{word}} Collection",
        "{{word}} Adventures",
        "The {{word}} Legacy",
        "{{word}} and {{word_2}}",
    ]

    # Book title templates
    title_templates = [
        "The {{word}}",
        "{{word}} and {{word_2}}",
        "The {{word}} of {{word_2}}",
        "{{word}}: A {{genre}} Story",
        "The Last {{word}}",
        "The Secret {{word}}",
        "A {{word}} in {{word_2}}",
        "The {{word}}'s {{word_2}}",
        "Beyond {{word}}",
        "{{word}} Rising",
        "The {{word}} Affair",
        "{{word}} Dreams",
        "Shadows of {{word}}",
        "The {{word}} Prophecy",
        "{{word}} Awakening",
    ]

    # Title words
    title_words = [
        "Shadow", "Light", "Dark", "Night", "Dawn", "Dusk", "Moon", "Sun",
        "Star", "Fire", "Ice", "Storm", "Wind", "Rain", "Thunder", "Sky",
        "Ocean", "Mountain", "River", "Forest", "Garden", "Kingdom", "Empire",
        "Crown", "Throne", "Sword", "Shield", "Dragon", "Phoenix", "Wolf",
        "Lion", "Eagle", "Rose", "Thorn", "Blood", "Stone", "Crystal",
        "Silver", "Golden", "Crimson", "Emerald", "Sapphire", "Ruby",
        "Time", "Destiny", "Fate", "Dream", "Memory", "Secret", "Mystery",
        "Truth", "Lie", "Hope", "Fear", "Love", "Death", "Life", "Soul"
    ]

    # Chapter title templates
    chapter_templates = [
        "Chapter {{number}}: {{word}}",
        "{{number}}. The {{word}}",
        "Part {{number}}: {{word}} and {{word_2}}",
        "{{word}}",
        "The {{word}} Begins",
        "{{word}}'s End",
    ]

    # Literary awards
    literary_awards = [
        "Pulitzer Prize", "Nobel Prize in Literature", "Man Booker Prize",
        "National Book Award", "Hugo Award", "Nebula Award",
        "Edgar Award", "Newbery Medal", "Caldecott Medal",
        "PEN/Faulkner Award", "Costa Book Award", "Baileys Women's Prize",
        "National Book Critics Circle Award", "Los Angeles Times Book Prize",
        "Goodreads Choice Award", "New York Times Bestseller"
    ]

    # Reading levels
    reading_levels = [
        "Early Reader", "Chapter Book", "Middle Grade", "Young Adult",
        "New Adult", "Adult", "Advanced"
    ]

    # Book conditions
    book_conditions = [
        "New", "Like New", "Very Good", "Good", "Acceptable",
        "Fair", "Poor", "Collectible", "First Edition", "Signed Copy"
    ]

    # Literary terms
    literary_terms = [
        "Protagonist", "Antagonist", "Plot", "Setting", "Theme",
        "Conflict", "Resolution", "Climax", "Foreshadowing", "Flashback",
        "Metaphor", "Simile", "Allegory", "Symbolism", "Irony",
        "Point of View", "Narrator", "Character Development", "Dialogue",
        "Exposition", "Rising Action", "Falling Action", "Denouement"
    ]

    # Book clubs/reading groups
    book_club_types = [
        "Book Club", "Reading Group", "Literary Circle", "Book Discussion",
        "Reading Society", "Literature Club", "Book Lovers Group"
    ]

    # Bookstore types
    bookstore_types = [
        "Independent Bookstore", "Chain Bookstore", "Used Bookstore",
        "Antiquarian Bookstore", "Online Bookstore", "University Bookstore",
        "Specialty Bookstore", "Comic Book Store", "Children's Bookstore"
    ]

    def book_title(self) -> str:
        """
        Generate a random book title.
        
        :example: 'The Shadow of Time'
        """
        template = self.random_element(self.title_templates)
        result = template
        
        # Replace placeholders
        if "{{word}}" in result:
            result = result.replace("{{word}}", self.random_element(self.title_words))
        if "{{word_2}}" in result:
            result = result.replace("{{word_2}}", self.random_element(self.title_words))
        if "{{genre}}" in result:
            result = result.replace("{{genre}}", self.random_element(self.literary_genres))
        
        return result

    def author_name(self) -> str:
        """
        Generate a random author name.
        
        :example: 'Jane Smith'
        """
        return self.generator.parse("{{first_name}} {{last_name}}")

    def literary_genre(self) -> str:
        """
        Generate a random literary genre.
        
        :example: 'Science Fiction'
        """
        return self.random_element(self.literary_genres)

    def publisher(self) -> str:
        """
        Generate a random publisher name.
        
        :example: 'Penguin Random House'
        """
        return self.random_element(self.publishers)

    def book_format(self) -> str:
        """
        Generate a random book format.
        
        :example: 'Hardcover'
        """
        return self.random_element(self.book_formats)

    def book_series(self) -> str:
        """
        Generate a random book series name.
        
        :example: 'The Dragon Chronicles'
        """
        template = self.random_element(self.series_templates)
        result = template
        
        if "{{word}}" in result:
            result = result.replace("{{word}}", self.random_element(self.title_words))
        if "{{word_2}}" in result:
            result = result.replace("{{word_2}}", self.random_element(self.title_words))
        
        return result

    def chapter_title(self, chapter_number: int = None) -> str:
        """
        Generate a random chapter title.
        
        :param chapter_number: Optional chapter number (default: random 1-30)
        :example: 'Chapter 5: The Shadow'
        """
        if chapter_number is None:
            chapter_number = self.random_int(1, 30)
        
        template = self.random_element(self.chapter_templates)
        result = template
        
        if "{{number}}" in result:
            result = result.replace("{{number}}", str(chapter_number))
        if "{{word}}" in result:
            result = result.replace("{{word}}", self.random_element(self.title_words))
        if "{{word_2}}" in result:
            result = result.replace("{{word_2}}", self.random_element(self.title_words))
        
        return result

    def literary_award(self) -> str:
        """
        Generate a random literary award name.
        
        :example: 'Pulitzer Prize'
        """
        return self.random_element(self.literary_awards)

    def reading_level(self) -> str:
        """
        Generate a random reading level.
        
        :example: 'Young Adult'
        """
        return self.random_element(self.reading_levels)

    def book_condition(self) -> str:
        """
        Generate a random book condition.
        
        :example: 'Like New'
        """
        return self.random_element(self.book_conditions)

    def literary_term(self) -> str:
        """
        Generate a random literary term.
        
        :example: 'Protagonist'
        """
        return self.random_element(self.literary_terms)

    def book_club_type(self) -> str:
        """
        Generate a random book club type.
        
        :example: 'Book Club'
        """
        return self.random_element(self.book_club_types)

    def bookstore_type(self) -> str:
        """
        Generate a random bookstore type.
        
        :example: 'Independent Bookstore'
        """
        return self.random_element(self.bookstore_types)

    def publication_year(self, min_year: int = 1900, max_year: int = 2024) -> int:
        """
        Generate a random publication year.
        
        :param min_year: Minimum year (default: 1900)
        :param max_year: Maximum year (default: 2024)
        :example: 2015
        """
        return self.random_int(min_year, max_year)

    def page_count(self, min_pages: int = 100, max_pages: int = 800) -> int:
        """
        Generate a random page count.
        
        :param min_pages: Minimum pages (default: 100)
        :param max_pages: Maximum pages (default: 800)
        :example: 342
        """
        return self.random_int(min_pages, max_pages)

    def book_price(self, min_price: float = 5.0, max_price: float = 50.0) -> str:
        """
        Generate a random book price.
        
        :param min_price: Minimum price (default: 5.0)
        :param max_price: Maximum price (default: 50.0)
        :example: '$24.99'
        """
        price = self.random_int(int(min_price * 100), int(max_price * 100)) / 100
        return f"${price:.2f}"

    def isbn(self) -> str:
        """
        Generate a random ISBN-13 number.
        
        :example: '978-3-16-148410-0'
        """
        # Generate ISBN-13 format
        prefix = "978"
        group = str(self.random_int(0, 9))
        publisher_code = str(self.random_int(10, 99))
        title_code = str(self.random_int(10000, 99999))
        
        # Calculate check digit (simplified)
        isbn_without_check = f"{prefix}{group}{publisher_code}{title_code}"
        check_digit = self.random_int(0, 9)
        
        return f"{prefix}-{group}-{publisher_code}-{title_code}-{check_digit}"

    def book_rating(self, min_rating: float = 1.0, max_rating: float = 5.0) -> float:
        """
        Generate a random book rating.
        
        :param min_rating: Minimum rating (default: 1.0)
        :param max_rating: Maximum rating (default: 5.0)
        :example: 4.2
        """
        rating = self.random_int(int(min_rating * 10), int(max_rating * 10)) / 10
        return rating

    def review_count(self, min_reviews: int = 10, max_reviews: int = 10000) -> int:
        """
        Generate a random review count.
        
        :param min_reviews: Minimum reviews (default: 10)
        :param max_reviews: Maximum reviews (default: 10000)
        :example: 1523
        """
        return self.random_int(min_reviews, max_reviews)

    def edition(self) -> str:
        """
        Generate a random book edition.
        
        :example: '2nd Edition'
        """
        editions = [
            "1st Edition", "2nd Edition", "3rd Edition", "4th Edition",
            "5th Edition", "Revised Edition", "Special Edition",
            "Anniversary Edition", "Deluxe Edition", "Collector's Edition",
            "Limited Edition", "Illustrated Edition", "Annotated Edition"
        ]
        return self.random_element(editions)

    def language(self) -> str:
        """
        Generate a random book language.
        
        :example: 'English'
        """
        languages = [
            "English", "Spanish", "French", "German", "Italian", "Portuguese",
            "Russian", "Chinese", "Japanese", "Korean", "Arabic", "Hindi",
            "Dutch", "Swedish", "Norwegian", "Danish", "Polish", "Turkish"
        ]
        return self.random_element(languages)
