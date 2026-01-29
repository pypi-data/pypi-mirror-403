from .. import BaseProvider

localized = False


class Provider(BaseProvider):
    """Provider for music-related data."""

    # Music genres
    music_genres = [
        "Rock", "Pop", "Hip Hop", "Jazz", "Blues", "Country", "Classical",
        "Electronic", "R&B", "Soul", "Funk", "Disco", "Reggae", "Punk",
        "Metal", "Alternative", "Indie", "Folk", "Gospel", "Latin",
        "World Music", "Dance", "House", "Techno", "Trance", "Dubstep",
        "Drum and Bass", "Ambient", "Experimental", "Ska", "Grunge",
        "Emo", "Hardcore", "Progressive Rock", "Psychedelic", "Bluegrass",
        "Opera", "Symphony", "Chamber Music", "K-Pop", "J-Pop", "Afrobeat",
        "Bossa Nova", "Flamenco", "Salsa", "Merengue", "Cumbia", "Tango"
    ]

    # Musical instruments
    instruments = [
        # String instruments
        "Guitar", "Electric Guitar", "Bass Guitar", "Acoustic Guitar",
        "Violin", "Viola", "Cello", "Double Bass", "Harp", "Ukulele",
        "Banjo", "Mandolin", "Sitar", "Lute",
        
        # Wind instruments
        "Flute", "Clarinet", "Oboe", "Bassoon", "Saxophone", "Trumpet",
        "Trombone", "French Horn", "Tuba", "Harmonica", "Recorder",
        "Piccolo", "Bagpipes", "Pan Flute",
        
        # Percussion instruments
        "Drums", "Drum Kit", "Snare Drum", "Bass Drum", "Timpani",
        "Xylophone", "Marimba", "Vibraphone", "Cymbals", "Tambourine",
        "Bongos", "Congas", "Djembe", "Tabla", "Gong",
        
        # Keyboard instruments
        "Piano", "Grand Piano", "Electric Piano", "Keyboard", "Organ",
        "Synthesizer", "Accordion", "Harpsichord", "Celesta"
    ]

    # Song title templates
    song_title_templates = [
        "{{word}} {{word_2}}",
        "{{word}} in the {{word_2}}",
        "{{word}} of {{word_2}}",
        "The {{word}}",
        "{{word}} Me",
        "I {{verb}} {{word}}",
        "{{word}} Tonight",
        "{{word}} Forever",
        "{{word}} Dreams",
        "{{word}} Heart",
        "{{word}} Soul",
        "{{word}} Love",
        "{{word}} Blues",
        "{{word}} Song",
        "{{word}} Nights",
        "{{word}} Days",
        "{{word}} Rain",
        "{{word}} Sun",
        "{{word}} Moon",
        "{{word}} Star",
    ]

    # Album name templates
    album_name_templates = [
        "{{word}}",
        "The {{word}}",
        "{{word}} {{word_2}}",
        "{{word}} and {{word_2}}",
        "{{word}}: {{word_2}}",
        "{{word}} Chronicles",
        "{{word}} Sessions",
        "{{word}} Collection",
        "{{word}} Experience",
        "{{word}} Journey",
        "{{word}} Anthology",
        "{{word}} Memories",
        "{{word}} Stories",
        "Greatest {{word}}",
        "Best of {{word}}",
    ]

    # Artist/Band name templates
    artist_name_templates = [
        "{{last_name}}",
        "{{first_name}} {{last_name}}",
        "{{word}} {{word_2}}",
        "The {{word}}s",
        "The {{word}} {{word_2}}s",
        "{{word}} and the {{word_2}}s",
        "{{first_name}} and the {{word}}s",
        "DJ {{last_name}}",
        "MC {{first_name}}",
        "{{word}} {{last_name}}",
        "{{first_name}} {{word}}",
    ]

    # Record labels
    record_labels = [
        "Atlantic Records", "Capitol Records", "Columbia Records",
        "Def Jam Recordings", "Elektra Records", "Epic Records",
        "Interscope Records", "Island Records", "RCA Records",
        "Republic Records", "Universal Music Group", "Warner Music Group",
        "Sony Music", "EMI Records", "Motown Records", "Geffen Records",
        "Virgin Records", "Parlophone", "Polydor Records", "Decca Records",
        "Blue Note Records", "Sub Pop", "4AD", "Merge Records",
        "Matador Records", "XL Recordings", "Domino Recording Company",
        "Rough Trade Records", "Warp Records", "Ninja Tune"
    ]

    # Music formats
    music_formats = [
        "MP3", "WAV", "FLAC", "AAC", "OGG", "WMA", "ALAC", "AIFF",
        "Vinyl", "CD", "Cassette", "Digital Download", "Streaming"
    ]

    # Music streaming platforms
    streaming_platforms = [
        "Spotify", "Apple Music", "YouTube Music", "Amazon Music",
        "Tidal", "Deezer", "Pandora", "SoundCloud", "Bandcamp",
        "Qobuz", "iHeartRadio", "TuneIn"
    ]

    # Concert venues
    concert_venues = [
        "Madison Square Garden", "The O2 Arena", "Wembley Stadium",
        "Red Rocks Amphitheatre", "Hollywood Bowl", "Royal Albert Hall",
        "Carnegie Hall", "Sydney Opera House", "Coachella Valley",
        "Glastonbury Festival", "Lollapalooza", "Bonnaroo",
        "Austin City Limits", "SXSW", "Burning Man"
    ]

    # Music awards
    music_awards = [
        "Grammy Award", "MTV Video Music Award", "American Music Award",
        "Billboard Music Award", "BET Award", "Country Music Award",
        "Latin Grammy", "BRIT Award", "Juno Award", "ARIA Award",
        "Mercury Prize", "Pulitzer Prize for Music"
    ]

    # Musical terms
    musical_terms = [
        "Tempo", "Rhythm", "Melody", "Harmony", "Chord", "Scale",
        "Octave", "Beat", "Measure", "Key", "Pitch", "Tone",
        "Timbre", "Dynamics", "Crescendo", "Diminuendo", "Forte",
        "Piano", "Allegro", "Adagio", "Andante", "Presto"
    ]

    # Song verbs for templates
    song_verbs = [
        "Love", "Need", "Want", "Miss", "Remember", "Forget",
        "Dance", "Sing", "Cry", "Smile", "Dream", "Believe"
    ]

    # Words for song/album titles
    title_words = [
        "Love", "Heart", "Soul", "Dream", "Night", "Day", "Star",
        "Moon", "Sun", "Fire", "Rain", "Storm", "Wind", "Ocean",
        "Mountain", "River", "Sky", "Light", "Dark", "Shadow",
        "Angel", "Devil", "Heaven", "Hell", "Paradise", "Midnight",
        "Dawn", "Dusk", "Summer", "Winter", "Spring", "Fall",
        "Wild", "Free", "Lost", "Found", "Broken", "Beautiful",
        "Sweet", "Bitter", "Golden", "Silver", "Blue", "Red",
        "Black", "White", "Electric", "Acoustic", "Neon", "Crystal"
    ]

    def music_genre(self) -> str:
        """
        Generate a random music genre.
        
        :example: 'Rock'
        """
        return self.random_element(self.music_genres)

    def instrument(self) -> str:
        """
        Generate a random musical instrument.
        
        :example: 'Guitar'
        """
        return self.random_element(self.instruments)

    def song_title(self) -> str:
        """
        Generate a random song title.
        
        :example: 'Dancing in the Moonlight'
        """
        template = self.random_element(self.song_title_templates)
        # Replace placeholders manually (not using generator.parse for custom placeholders)
        result = template
        if "{{word}}" in result:
            result = result.replace("{{word}}", self.random_element(self.title_words))
        if "{{word_2}}" in result:
            result = result.replace("{{word_2}}", self.random_element(self.title_words))
        if "{{verb}}" in result:
            result = result.replace("{{verb}}", self.random_element(self.song_verbs))
        return result

    def album_name(self) -> str:
        """
        Generate a random album name.
        
        :example: 'The Dark Side'
        """
        template = self.random_element(self.album_name_templates)
        # Replace placeholders manually
        result = template
        if "{{word}}" in result:
            result = result.replace("{{word}}", self.random_element(self.title_words))
        if "{{word_2}}" in result:
            result = result.replace("{{word_2}}", self.random_element(self.title_words))
        return result

    def artist_name(self) -> str:
        """
        Generate a random artist name.
        
        :example: 'John Smith'
        """
        template = self.random_element(self.artist_name_templates)
        # First replace person name placeholders using generator
        if "{{first_name}}" in template or "{{last_name}}" in template:
            result = self.generator.parse(template)
        else:
            result = template
        # Then replace word placeholders manually
        if "{{word}}" in result:
            result = result.replace("{{word}}", self.random_element(self.title_words))
        if "{{word_2}}" in result:
            result = result.replace("{{word_2}}", self.random_element(self.title_words))
        return result

    def band_name(self) -> str:
        """
        Generate a random band name.
        
        :example: 'The Rolling Stones'
        """
        # Use templates that are more band-oriented
        band_templates = [
            "The {{word}}s",
            "The {{word}} {{word_2}}s",
            "{{word}} and the {{word_2}}s",
            "{{word}} {{word_2}}",
        ]
        template = self.random_element(band_templates)
        result = template
        if "{{word}}" in result:
            result = result.replace("{{word}}", self.random_element(self.title_words))
        if "{{word_2}}" in result:
            result = result.replace("{{word_2}}", self.random_element(self.title_words))
        return result

    def record_label(self) -> str:
        """
        Generate a random record label name.
        
        :example: 'Atlantic Records'
        """
        return self.random_element(self.record_labels)

    def music_format(self) -> str:
        """
        Generate a random music format.
        
        :example: 'MP3'
        """
        return self.random_element(self.music_formats)

    def streaming_platform(self) -> str:
        """
        Generate a random music streaming platform.
        
        :example: 'Spotify'
        """
        return self.random_element(self.streaming_platforms)

    def concert_venue(self) -> str:
        """
        Generate a random concert venue or festival name.
        
        :example: 'Madison Square Garden'
        """
        return self.random_element(self.concert_venues)

    def music_award(self) -> str:
        """
        Generate a random music award name.
        
        :example: 'Grammy Award'
        """
        return self.random_element(self.music_awards)

    def musical_term(self) -> str:
        """
        Generate a random musical term.
        
        :example: 'Tempo'
        """
        return self.random_element(self.musical_terms)

    def song_duration(self, min_seconds: int = 120, max_seconds: int = 360) -> str:
        """
        Generate a random song duration in MM:SS format.
        
        :param min_seconds: Minimum duration in seconds (default: 120 = 2:00)
        :param max_seconds: Maximum duration in seconds (default: 360 = 6:00)
        :example: '3:45'
        """
        total_seconds = self.random_int(min_seconds, max_seconds)
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"{minutes}:{seconds:02d}"

    def album_year(self, min_year: int = 1950, max_year: int = 2024) -> int:
        """
        Generate a random album release year.
        
        :param min_year: Minimum year (default: 1950)
        :param max_year: Maximum year (default: 2024)
        :example: 1999
        """
        return self.random_int(min_year, max_year)

    def track_number(self, max_tracks: int = 15) -> int:
        """
        Generate a random track number.
        
        :param max_tracks: Maximum number of tracks (default: 15)
        :example: 7
        """
        return self.random_int(1, max_tracks)

    def bpm(self, min_bpm: int = 60, max_bpm: int = 180) -> int:
        """
        Generate a random BPM (Beats Per Minute).
        
        :param min_bpm: Minimum BPM (default: 60)
        :param max_bpm: Maximum BPM (default: 180)
        :example: 120
        """
        return self.random_int(min_bpm, max_bpm)

    def music_key(self) -> str:
        """
        Generate a random musical key.
        
        :example: 'C Major'
        """
        notes = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
        scales = ["Major", "Minor"]
        return f"{self.random_element(notes)} {self.random_element(scales)}"

    def playlist_name(self) -> str:
        """
        Generate a random playlist name.
        
        :example: 'Summer Vibes'
        """
        playlist_templates = [
            "{{word}} Vibes",
            "{{word}} Mix",
            "{{word}} Playlist",
            "{{word}} Hits",
            "Best of {{word}}",
            "{{word}} Classics",
            "{{word}} Favorites",
            "{{word}} Collection",
            "{{word}} {{word_2}}",
            "My {{word}} Playlist",
        ]
        template = self.random_element(playlist_templates)
        result = template
        if "{{word}}" in result:
            result = result.replace("{{word}}", self.random_element(self.title_words))
        if "{{word_2}}" in result:
            result = result.replace("{{word_2}}", self.random_element(self.title_words))
        return result
