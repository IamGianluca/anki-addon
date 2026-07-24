import re

from addon.infrastructure.protocols import ConfigProvider


class FakeMainWindow:
    def __init__(self, collection):
        self.col = collection


class FakeAddonManager(ConfigProvider):
    def __init__(self, config: dict):
        self._config = config

    def getConfig(self, module: str) -> dict:
        return self._config


class FakeCollection:
    def __init__(self):
        self.notes = {}  # note_id -> note
        self.cards = {}  # card_id -> card
        self.decks = FakeDeckManager()
        self.models = FakeModelsManager()

    def get_note(self, note_id):
        return self.notes.get(note_id)

    def get_card(self, card_id):
        # Return the card with the given ID
        return self.cards.get(card_id)

    def find_notes(self, query):
        # Supports nid:<id>, did:<id>, and plain text terms (all terms
        # must appear, case-insensitive, across fields and tags).
        # Combined queries are not supported (no caller uses them).
        m = re.search(r"\bnid:(\d+)", query)
        if m:
            note_id = int(m.group(1))
            return [note_id] if note_id in self.notes else []
        m = re.search(r"\bdid:(\d+)", query)
        if m:
            if int(m.group(1)) == self.decks.current()["id"]:
                return list(self.notes.keys())
            return []
        terms = query.lower().split()
        if not terms:
            return list(self.notes.keys())
        return [
            note_id
            for note_id, note in self.notes.items()
            if all(term in _note_text(note) for term in terms)
        ]

    def new_note(self, notetype):
        fields = {f["name"]: "" for f in notetype["flds"]}
        # FakeNote reads its type marker from a "type" field
        fields["type"] = notetype.get("type", 0)
        return FakeNote(max(self.notes, default=0) + 1, fields)

    def add_note(self, note, deck_id):
        self.notes[note.id] = note

    def update_note(self, note):
        self.notes[note.id] = note
        note.flush()

    def remove_notes(self, note_ids):
        for note_id in note_ids:
            self.notes.pop(note_id, None)
        self.cards = {
            card_id: card
            for card_id, card in self.cards.items()
            if card.note_id not in note_ids
        }

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


def _note_text(note) -> str:
    fields = " ".join(str(note[key]) for key in note.keys())
    return f"{fields} {' '.join(note.tags)}".lower()


class FakeModelsManager:
    """By default provides the stock 'Basic' and 'Cloze' notetypes."""

    _BASIC = {
        "name": "Basic",
        "type": 0,
        "flds": [{"name": "Front"}, {"name": "Back"}],
    }
    _CLOZE = {
        "name": "Cloze",
        "type": 1,
        "flds": [{"name": "Text"}, {"name": "Back Extra"}],
    }

    def __init__(self, notetypes=None):
        if notetypes is None:
            notetypes = [self._BASIC, self._CLOZE]
        self._notetypes = notetypes

    def by_name(self, name):
        for notetype in self._notetypes:
            if notetype["name"] == name:
                return notetype
        return None


class FakeDeckManager:
    def __init__(self):
        self.current_deck = {"id": 1, "name": "Default"}

    def current(self):
        return self.current_deck

    def id_for_name(self, name):
        if name == self.current_deck["name"]:
            return self.current_deck["id"]
        return None


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

    def note_type(self) -> dict:
        note_type = self._fields.get("type", 0)  # 0 = basic, 1 = cloze
        return dict(type=note_type)

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
