"""
Hardcoded PTP metadata from upload.php
"""

import enum
import re

types = {
    'Feature Film': re.compile(r'^(?i:(?:feature|).?film|movie)$'),
    'Short Film': re.compile(r'^(?i:short.?(?:film|))$'),
    'Miniseries': re.compile(r'^(?i:(?:mini.?|)series|season|tv)$'),
    'Stand-up Comedy': re.compile(r'^(?i:stand.?up.?comedy|stand.?up|comedy)$'),
    'Live Performance': re.compile(r'(?i:live.?performance|live|performance)$'),
    'Movie Collection': re.compile(r'(?i:movie.?collection|collection)$'),
}


sources = {
    'Blu-ray': re.compile(r'(?i:blu-?ray|bd(?:25|50|66|100))'),  # (UHD) BluRay|BD(25|50|66|100) (Remux)
    'DVD': re.compile(r'^(?i:dvd)'),  # DVD(Rip|5|9|...)
    'WEB': re.compile(r'^(?i:web)'),  # WEB(-DL|Rip)
    'HD-DVD': re.compile(r'^(?i:hd-?dvd)$'),
    'HDTV': re.compile(r'^(?i:hd-?tv)$'),
    'TV': re.compile(r'^(?i:(?:sd-?|)tv)'),  # TV(Rip|...)
    'VHS': re.compile(r'^(?i:vhs)'),  # VHS(Rip|...)
}


codecs = {
    # NOTE: We must check "source" before "video_format" because BD* contains H.264 or x264.
    'DVD5': lambda release: release.source == 'DVD5',
    'DVD9': lambda release: release.source == 'DVD9',
    'BD25': lambda release: release.source == 'BD25',
    'BD50': lambda release: release.source == 'BD50',
    'BD66': lambda release: release.source == 'BD66',
    'BD100': lambda release: release.source == 'BD100',
    'XviD': lambda release: release.video_format == 'XviD',
    'DivX': lambda release: release.video_format == 'DivX',
    'H.264': lambda release: release.video_format == 'H.264',
    'x264': lambda release: release.video_format == 'x264',
    'H.265': lambda release: release.video_format == 'H.265',
    'x265': lambda release: release.video_format == 'x265',
}


containers = {
    'AVI': lambda release: release.container == 'avi',
    'MPG': lambda release: release.container == 'mpg',
    'MKV': lambda release: release.container == 'mkv',
    'MP4': lambda release: release.container == 'mp4',
    'VOB IFO': lambda release: release.container == 'VIDEO_TS',
    'ISO': lambda release: release.container == 'iso',
    'm2ts': lambda release: release.container == 'BDMV',
}


resolutions = {
    'NTSC': lambda release: release.dvd_resolution == 'NTSC',
    'PAL': lambda release: release.dvd_resolution == 'PAL',
    '480p': lambda release: release.resolution == '480p',
    '576p': lambda release: release.resolution == '576p',
    '720p': lambda release: release.resolution == '720p',
    '1080i': lambda release: release.resolution == '1080i',
    '1080p': lambda release: release.resolution == '1080p',
    '2160p': lambda release: release.resolution == '2160p',
}


# NOTE: The order of the dictionaries and their elements are copied from
#       upload.php. They should be submitted in the same order as listed here.
editions = {
    'collection.criterion': 'The Criterion Collection',
    'collection.masters': 'Masters of Cinema',
    'collection.warner': 'Warner Archive Collection',

    'edition.dc': "Director's Cut",
    'edition.extended': 'Extended Edition',
    'edition.rifftrax': 'Rifftrax',
    'edition.theatrical': 'Theatrical Cut',
    'edition.uncut': 'Uncut',
    'edition.unrated': 'Unrated',

    'feature.remux': 'Remux',
    'feature.2in1': '2in1',
    'feature.2disc': '2-Disc Set',
    'feature.3d_anaglyph': '3D Anaglyph',
    'feature.3d_full_sbs': '3D Full SBS',
    'feature.3d_half_ou': '3D Half OU',
    'feature.3D_half_sbs': '3D Half SBS',
    'feature.4krestoration': '4K Restoration',
    'feature.10bit': '10-bit',
    'feature.extras': 'Extras',
    'feature.4kremaster': '4K Remaster',
    'feature.2d3d_edition': '2D/3D Edition',
    'feature.dtsx': 'DTS:X',
    'feature.dolby_atmos': 'Dolby Atmos',
    'feature.dolby_vision': 'Dolby Vision',
    'feature.hdr10': 'HDR10',
    'feature.hdr10+': 'HDR10+',
    'feature.dual_audio': 'Dual Audio',
    'feature.english_dub': 'English Dub',
    'feature.commentary': 'With Commentary',
}


subtitles = {
    # Special codes
    'No Subtitles': '44',
    'en (forced)': '50',

    # TODO: No idea what intertitles are exactly and how to detect them.
    # 'English Intertitles': '51',

    # Regular languages
    'ar': '22',     # Arabic
    'bg': '29',     # Bulgarian
    'zh': '14',     # Chinese
    'hr': '23',     # Croatian
    'cs': '30',     # Czech
    'da': '10',     # Danish
    'nl': '9',      # Dutch
    'en': '3',      # English
    'et': '38',     # Estonian
    'fi': '15',     # Finnish
    'fr': '5',      # French
    'de': '6',      # German
    'el': '26',     # Greek
    'he': '40',     # Hebrew
    'hi': '41',     # Hindi
    'hu': '24',     # Hungarian
    'is': '28',     # Icelandic
    'id': '47',     # Indonesian
    'it': '16',     # Italian
    'ja': '8',      # Japanese
    'ko': '19',     # Korean
    'lv': '37',     # Latvian
    'lt': '39',     # Lithuanian
    'no': '12',     # Norwegian
    'fa': '52',     # Persian
    'pl': '17',     # Polish
    'pt': '21',     # Portuguese
    'pt-BR': '49',  # Brazilian Port.
    'ro': '13',     # Romanian
    'ru': '7',      # Russian
    'sr': '31',     # Serbian
    'sk': '42',     # Slovak
    'sl': '43',     # Slovenian
    'es': '4',      # Spanish
    'sv': '11',     # Swedish
    'th': '20',     # Thai
    'tr': '18',     # Turkish
    'uk': '34',     # Ukrainian
    'vi': '25',     # Vietnamese
}


class _PrettyEnum(enum.Enum):
    @classmethod
    def from_string(cls, string):
        """
        Convert human-readable string back to enum

        >>> TrumpableReason.from_string(
        ...     str(TrumpableReason.HARDCODED_SUBTITLES)
        ... )
        <TrumpableReason.HARDCODED_SUBTITLES: 4>

        :raise AttributeError: if `string` is not known
        """
        name = string.replace(' ', '_').upper()
        return getattr(cls, name)

    def __str__(self):
        return ' '.join(
            word.capitalize()
            for word in self.name.split('_')
        )


class TrumpableReason(_PrettyEnum):
    """
    Reason why a release is trumpable

    An instance's :attr:`value` is the value expected by the API. An instance's
    string representation should be human-readable and pretty.
    """

    NO_ENGLISH_SUBTITLES = 14
    HARDCODED_SUBTITLES = 4


class ArtistImportance(_PrettyEnum):
    """
    Purpose of a person in a movie

    An instance's :attr:`value` is the value expected by the API. An instance's
    string representation should be human-readable and pretty.
    """

    ACTOR = 5
    DIRECTOR = 1
    WRITER = 2
    PRODUCER = 3
    COMPOSER = 4
    CINEMATOGRAPHER = 6
