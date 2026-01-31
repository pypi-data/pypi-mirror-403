from dataclasses import dataclass
from typing import Optional

# Pitch-class canonical names (all sharps)
NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

# Aliases for normalization (flats, H, etc.)
NOTE_ALIASES = {
    "CB": "B",
    "B#": "C",
    "DB": "C#",
    "EB": "D#",
    "E#": "F",
    "FB": "E",
    "GB": "F#",
    "AB": "G#",
    "BB": "A#",
    "HB": "B",
    "H": "B",
}


def normalize_note_pc(note: str) -> Optional[str]:
    """Normalize pitch-class spelling to canonical sharp-based representation."""
    up = note.strip().upper()
    # Handle double sharp x
    if up.endswith("X"):
        base = up[:-1]
        if base in NOTE_NAMES or base in NOTE_ALIASES:
             # Recursively normalize base and add 2 semitones
             base_pc = normalize_note_pc(base)
             if base_pc:
                 idx = NOTE_NAMES.index(base_pc)
                 return NOTE_NAMES[(idx + 2) % 12]
    
    if up in NOTE_ALIASES:
        return NOTE_ALIASES[up]
    if up in NOTE_NAMES:
        return up
    return None


def normalize_spelling(token: str) -> str:
    """Keep user spelling but capitalize first letter (Db -> Db, c# -> C#)."""
    token = token.strip()
    if not token:
        return token
    return token[0].upper() + token[1:]


@dataclass
class ParsedChord:
    symbol: str
    root: str  # user spelling (e.g., Db / C#)
    quality: str
    bass: Optional[str] = None  # user spelling (e.g., F#, Gb)


class ChordParser:
    @staticmethod
    def parse(symbol: str) -> Optional[ParsedChord]:
        """Parse chord symbol like 'C#m7/G#' into components."""
        if not symbol:
            return None

        text = symbol.strip()

        # Allow no-chord markers
        normalized_nc = text.replace(".", "").replace(" ", "").upper()
        if normalized_nc in {"NC", "NOCHORD"}:
            return ParsedChord(symbol=text, root="NC", quality="", bass=None)

        # Split slash bass if present
        if "/" in text:
            body, bass = text.split("/", 1)
            bass_token = bass.strip()
            if normalize_note_pc(bass_token) is None:
                return None
        else:
            body, bass_token = text, None

        body = body.strip()
        if not body:
            return None

        # Root token: A-G plus optional accidentals (#, b, x, bb)
        # Check for 2-char accidentals first (bb) or just double #?
        # Actually user input might be "Cbb". body="Cbb".
        # Or "Cx". body="Cx".
        
        # Simple parser approach:
        # Take 1 char. Check next chars for accidentals.
        root_len = 1
        if len(body) > 1 and body[1] in ("#", "b", "B", "x", "X"):
             root_len = 2
             # Check for double accidentals like "bb" or "##"
             if len(body) > 2 and body[2] == body[1] and body[1] in ("#", "b", "B"):
                 root_len = 3
        
        root_token = body[:root_len]
        rest = body[root_len:]

        # Validate root
        if normalize_note_pc(root_token) is None:
            return None

        root = normalize_spelling(root_token)
        quality = rest or ""

        bass: Optional[str] = None
        if bass_token:
            bass = normalize_spelling(bass_token)

        return ParsedChord(symbol=text, root=root, quality=quality, bass=bass)
