class FakeMainWindow:
    def __init__(self, collection):
        self.col = collection


class FakeCollection:
    def __init__(self):
        self.notes = {}  # note_id -> note
        self.cards = {}  # card_id -> card
        self.decks = FakeDeckManager()

    def get_note(self, note_id):
        return self.notes.get(note_id)

    def get_card(self, card_id):
        # Return the card with the given ID
        return self.cards.get(card_id)

    def find_notes(self, query):
        # Simple implementation that returns all notes if query contains "did:"
        if "did:" in query:
            return list(self.notes.keys())
        return []

    def find_cards(self, query):
        # Simple implementation that returns card IDs for a note ID
        # Parse query like "nid:1" to get note_id
        if query.startswith("nid:"):
            note_id = int(query[4:])
            # Return list of card IDs associated with this note ID
            # In a real implementation, you'd look up the actual relationships
            return [
                card_id
                for card_id, card in self.cards.items()
                if getattr(card, "note_id", None) == note_id
            ]
        return []


class FakeDeckManager:
    def __init__(self):
        self.current_deck = {"id": 1, "name": "Default"}

    def current(self):
        return self.current_deck


class FakeNote:
    """A simplified version of Anki's Note class for testing purposes.
    Only implements the essential functionality needed for basic operations.
    """

    def __init__(self, note_id, fields=None):
        self.id = note_id
        self.guid = str(self.id)  # TODO: properly implement guid
        self._fields = fields or {}
        self.model = {"flds": [{"name": k} for k in self._fields.keys()]}
        self.tags = []
        self._was_flushed = False

    def keys(self):
        return self._fields.keys()

    def __getitem__(self, key):
        return self._fields.get(key, "")

    def __setitem__(self, key, value):
        self._fields[key] = value

    def flush(self) -> None:
        self._was_flushed = True

    # Helper method for testing
    def was_flushed(self) -> bool:
        return self._was_flushed


class FakeCard:
    """A simplified version of Anki's Card class for testing purposes.
    Only implements the essential functionality needed for basic operations.
    """

    def __init__(self, card_id, note_id, flags=0) -> None:
        self.id = card_id
        self.note_id = note_id
        self.flags = flags
        self._was_flushed = False

    def flush(self) -> None:
        """Simulate saving the card to the database"""
        self._was_flushed = True

    # Helper method for testing
    def was_flushed(self) -> bool:
        return self._was_flushed
