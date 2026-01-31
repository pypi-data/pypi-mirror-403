import mimetypes
import string

from hypothesis import strategies as st

EXTENSIONS = set(mimetypes.types_map.keys())
EMPTY_NAMES = {"", " ", ".", ".."}

# --- Media type strategies ---

extensions = st.sampled_from(sorted(EXTENSIONS))

# --- Alphabet strategies ---

cyrillic = st.characters(
    min_codepoint=0x0400,
    max_codepoint=0x04FF,
    blacklist_categories=("Cn", "Cs"),
)
greek = st.characters(
    min_codepoint=0x0370,
    max_codepoint=0x03FF,
    blacklist_categories=("Cn", "Cs"),
)

# --- File strategies ---

filename_chars = st.one_of(
    st.sampled_from(string.ascii_letters + string.digits + "._-()[]{}@+, "),
    cyrillic,
    greek,
).filter(lambda x: x not in EMPTY_NAMES)


@st.composite
def filenames(draw):
    name = draw(st.text(filename_chars, min_size=1))
    extension = draw(extensions)
    return name + extension
