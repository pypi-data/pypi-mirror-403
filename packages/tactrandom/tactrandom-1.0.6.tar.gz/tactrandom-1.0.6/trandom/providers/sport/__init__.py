from .. import BaseProvider

localized = False


class Provider(BaseProvider):
    """Provider for sport-related data."""

    # Sports categories
    sports = [
        # Ball sports
        "Football", "Soccer", "Basketball", "Baseball", "Tennis", "Volleyball",
        "Cricket", "Rugby", "Golf", "Table Tennis", "Badminton", "Handball",
        "Squash", "Racquetball", "Lacrosse", "Field Hockey", "Ice Hockey",
        "Water Polo", "Polo", "Softball", "Beach Volleyball",
        
        # Combat sports
        "Boxing", "Wrestling", "Judo", "Karate", "Taekwondo", "Kickboxing",
        "Mixed Martial Arts", "Fencing", "Sumo Wrestling", "Muay Thai",
        
        # Water sports
        "Swimming", "Diving", "Surfing", "Water Skiing", "Wakeboarding",
        "Rowing", "Kayaking", "Canoeing", "Sailing", "Windsurfing",
        
        # Winter sports
        "Skiing", "Snowboarding", "Ice Skating", "Figure Skating", "Speed Skating",
        "Curling", "Bobsled", "Luge", "Biathlon", "Cross-Country Skiing",
        
        # Athletics
        "Track and Field", "Marathon", "Sprinting", "Long Jump", "High Jump",
        "Pole Vault", "Shot Put", "Discus Throw", "Javelin Throw", "Hurdles",
        
        # Other sports
        "Cycling", "Mountain Biking", "Gymnastics", "Weightlifting", "Archery",
        "Shooting", "Equestrian", "Rock Climbing", "Skateboarding", "BMX",
        "Triathlon", "Decathlon", "Pentathlon"
    ]

    # Team sports
    team_sports = [
        "Football", "Soccer", "Basketball", "Baseball", "Volleyball", "Cricket",
        "Rugby", "Handball", "Field Hockey", "Ice Hockey", "Water Polo",
        "Lacrosse", "Softball", "Beach Volleyball"
    ]

    # Individual sports
    individual_sports = [
        "Tennis", "Golf", "Boxing", "Swimming", "Gymnastics", "Track and Field",
        "Cycling", "Skiing", "Snowboarding", "Surfing", "Skateboarding",
        "Archery", "Shooting", "Fencing", "Wrestling", "Judo", "Karate"
    ]

    # Olympic sports
    olympic_sports = [
        "Athletics", "Swimming", "Gymnastics", "Basketball", "Football",
        "Volleyball", "Tennis", "Boxing", "Wrestling", "Judo", "Taekwondo",
        "Fencing", "Archery", "Shooting", "Cycling", "Rowing", "Sailing",
        "Diving", "Water Polo", "Handball", "Hockey", "Rugby", "Golf",
        "Surfing", "Skateboarding", "Sport Climbing", "Karate", "Badminton",
        "Table Tennis", "Weightlifting", "Triathlon", "Modern Pentathlon"
    ]

    # Sports positions (generic)
    positions = [
        # General positions
        "Forward", "Midfielder", "Defender", "Goalkeeper", "Center", "Guard",
        "Striker", "Winger", "Fullback", "Halfback", "Quarterback", "Running Back",
        "Wide Receiver", "Tight End", "Linebacker", "Cornerback", "Safety",
        "Pitcher", "Catcher", "Infielder", "Outfielder", "Point Guard",
        "Shooting Guard", "Small Forward", "Power Forward", "Center Back",
        "Left Back", "Right Back", "Defensive Midfielder", "Attacking Midfielder"
    ]

    # Sports equipment
    equipment = [
        "Ball", "Bat", "Racket", "Club", "Stick", "Puck", "Net", "Goal",
        "Helmet", "Pads", "Gloves", "Cleats", "Shoes", "Jersey", "Shorts",
        "Shin Guards", "Mouthguard", "Goggles", "Swimsuit", "Skis", "Snowboard",
        "Skateboard", "Bicycle", "Surfboard", "Kayak", "Canoe", "Rowing Machine",
        "Weights", "Barbell", "Dumbbell", "Kettlebell", "Jump Rope", "Mat",
        "Punching Bag", "Boxing Gloves", "Fencing Sword", "Bow and Arrow",
        "Target", "Stopwatch", "Whistle", "Scoreboard"
    ]

    # Sports venues
    venues = [
        "Stadium", "Arena", "Court", "Field", "Pitch", "Track", "Pool",
        "Rink", "Gym", "Gymnasium", "Sports Complex", "Coliseum", "Dome",
        "Ballpark", "Golf Course", "Tennis Court", "Basketball Court",
        "Soccer Field", "Football Stadium", "Baseball Diamond", "Ice Rink",
        "Swimming Pool", "Velodrome", "Ski Resort", "Skate Park"
    ]

    # Famous sports venues
    famous_venues = [
        "Wembley Stadium", "Madison Square Garden", "Camp Nou", "Old Trafford",
        "Yankee Stadium", "Fenway Park", "Wimbledon", "Augusta National",
        "Melbourne Cricket Ground", "Maracanã Stadium", "San Siro",
        "Allianz Arena", "Santiago Bernabéu", "Anfield", "Emirates Stadium",
        "Staples Center", "TD Garden", "United Center", "Oracle Arena"
    ]

    # Sports leagues
    leagues = [
        "NFL", "NBA", "MLB", "NHL", "MLS", "Premier League", "La Liga",
        "Serie A", "Bundesliga", "Ligue 1", "UEFA Champions League",
        "FIFA World Cup", "Olympics", "NCAA", "ATP Tour", "WTA Tour",
        "PGA Tour", "Formula 1", "NASCAR", "IndyCar", "UFC", "WWE"
    ]

    # Sports awards
    awards = [
        "MVP", "Rookie of the Year", "Coach of the Year", "Defensive Player of the Year",
        "Golden Boot", "Golden Ball", "Golden Glove", "Ballon d'Or",
        "Heisman Trophy", "Cy Young Award", "Gold Medal", "Silver Medal",
        "Bronze Medal", "Championship Trophy", "World Cup Trophy",
        "Stanley Cup", "Super Bowl Ring", "NBA Championship Ring",
        "Olympic Gold Medal", "Hall of Fame Induction"
    ]

    # Sports terms
    terms = [
        "Goal", "Score", "Point", "Touchdown", "Home Run", "Slam Dunk",
        "Hat Trick", "Grand Slam", "Ace", "Birdie", "Eagle", "Bogey",
        "Knockout", "Submission", "Pin", "Checkmate", "Serve", "Volley",
        "Dribble", "Pass", "Tackle", "Block", "Steal", "Rebound",
        "Assist", "Penalty", "Foul", "Offside", "Timeout", "Overtime",
        "Sudden Death", "Playoff", "Championship", "Tournament", "Match",
        "Game", "Set", "Round", "Quarter", "Half", "Inning", "Period"
    ]

    # Team name templates
    team_name_templates = [
        "{{city}} {{mascot}}",
        "{{word}} {{mascot}}",
        "The {{mascot}}",
        "{{city}} {{word}}",
    ]

    # Team mascots
    mascots = [
        "Lions", "Tigers", "Bears", "Eagles", "Hawks", "Falcons", "Ravens",
        "Cardinals", "Bulls", "Rams", "Broncos", "Colts", "Panthers",
        "Jaguars", "Dolphins", "Sharks", "Wolves", "Coyotes", "Wildcats",
        "Bulldogs", "Huskies", "Terriers", "Warriors", "Knights", "Spartans",
        "Trojans", "Vikings", "Pirates", "Raiders", "Rangers", "Giants",
        "Titans", "Thunder", "Lightning", "Storm", "Heat", "Suns", "Stars",
        "Flames", "Avalanche", "Hurricanes", "Cyclones", "Tornadoes"
    ]

    # Sport words for team names
    sport_words = [
        "United", "City", "Athletic", "Sporting", "Real", "Royal", "Olympic",
        "National", "International", "Metropolitan", "Capital", "Central"
    ]

    def sport(self) -> str:
        """
        Generate a random sport name.
        
        :example: 'Basketball'
        """
        return self.random_element(self.sports)

    def team_sport(self) -> str:
        """
        Generate a random team sport name.
        
        :example: 'Football'
        """
        return self.random_element(self.team_sports)

    def individual_sport(self) -> str:
        """
        Generate a random individual sport name.
        
        :example: 'Tennis'
        """
        return self.random_element(self.individual_sports)

    def olympic_sport(self) -> str:
        """
        Generate a random Olympic sport name.
        
        :example: 'Swimming'
        """
        return self.random_element(self.olympic_sports)

    def sport_position(self) -> str:
        """
        Generate a random sport position.
        
        :example: 'Quarterback'
        """
        return self.random_element(self.positions)

    def sport_equipment(self) -> str:
        """
        Generate a random sport equipment item.
        
        :example: 'Ball'
        """
        return self.random_element(self.equipment)

    def sport_venue(self) -> str:
        """
        Generate a random sport venue type.
        
        :example: 'Stadium'
        """
        return self.random_element(self.venues)

    def famous_sport_venue(self) -> str:
        """
        Generate a random famous sport venue name.
        
        :example: 'Wembley Stadium'
        """
        return self.random_element(self.famous_venues)

    def sport_league(self) -> str:
        """
        Generate a random sport league or competition name.
        
        :example: 'NBA'
        """
        return self.random_element(self.leagues)

    def sport_award(self) -> str:
        """
        Generate a random sport award name.
        
        :example: 'MVP'
        """
        return self.random_element(self.awards)

    def sport_term(self) -> str:
        """
        Generate a random sport term.
        
        :example: 'Touchdown'
        """
        return self.random_element(self.terms)

    def team_name(self) -> str:
        """
        Generate a random team name.
        
        :example: 'Chicago Bulls'
        """
        template = self.random_element(self.team_name_templates)
        result = template
        
        # First replace custom placeholders manually (before generator.parse)
        if "{{mascot}}" in result:
            result = result.replace("{{mascot}}", self.random_element(self.mascots))
        if "{{word}}" in result:
            result = result.replace("{{word}}", self.random_element(self.sport_words))
        if "{{word_2}}" in result:
            result = result.replace("{{word_2}}", self.random_element(self.sport_words))
        
        # Then replace city placeholder using generator if present
        if "{{city}}" in result:
            result = self.generator.parse(result)
        
        return result

    def athlete_name(self) -> str:
        """
        Generate a random athlete name.
        
        :example: 'Michael Jordan'
        """
        return self.generator.parse("{{first_name}} {{last_name}}")

    def score(self, min_score: int = 0, max_score: int = 100) -> int:
        """
        Generate a random sport score.
        
        :param min_score: Minimum score (default: 0)
        :param max_score: Maximum score (default: 100)
        :example: 42
        """
        return self.random_int(min_score, max_score)

    def jersey_number(self, min_number: int = 0, max_number: int = 99) -> int:
        """
        Generate a random jersey number.
        
        :param min_number: Minimum number (default: 0)
        :param max_number: Maximum number (default: 99)
        :example: 23
        """
        return self.random_int(min_number, max_number)

    def season_year(self, min_year: int = 1950, max_year: int = 2024) -> str:
        """
        Generate a random season year in format 'YYYY-YY'.
        
        :param min_year: Minimum year (default: 1950)
        :param max_year: Maximum year (default: 2024)
        :example: '2023-24'
        """
        year = self.random_int(min_year, max_year)
        next_year = str(year + 1)[-2:]
        return f"{year}-{next_year}"

    def game_duration(self, min_minutes: int = 60, max_minutes: int = 120) -> str:
        """
        Generate a random game duration in MM:SS format.
        
        :param min_minutes: Minimum duration in minutes (default: 60)
        :param max_minutes: Maximum duration in minutes (default: 120)
        :example: '90:00'
        """
        minutes = self.random_int(min_minutes, max_minutes)
        seconds = self.random_int(0, 59)
        return f"{minutes}:{seconds:02d}"

    def record(self, wins_max: int = 82, losses_max: int = 82) -> str:
        """
        Generate a random win-loss record.
        
        :param wins_max: Maximum wins (default: 82)
        :param losses_max: Maximum losses (default: 82)
        :example: '45-37'
        """
        wins = self.random_int(0, wins_max)
        losses = self.random_int(0, losses_max)
        return f"{wins}-{losses}"

    def ranking(self, max_rank: int = 100) -> int:
        """
        Generate a random ranking position.
        
        :param max_rank: Maximum rank (default: 100)
        :example: 5
        """
        return self.random_int(1, max_rank)
