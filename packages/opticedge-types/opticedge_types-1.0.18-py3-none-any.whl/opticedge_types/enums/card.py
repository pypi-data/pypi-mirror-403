from enum import IntEnum, Enum

class ApprovalStatus(IntEnum):
    RESCAN = -2
    PENDING = -1
    FAILED = 0
    APPROVED = 1
    PENDING_INSTANT = 3
    APPROVING = 999


class RejectType(Enum):
    INVALID_CARD = "Invalid card"
    FAKE_HIGHRISK = "Fake - High Risk"
    REPEAT = "Repeat"
    MODEL_FAILURE = "Model failure"


class RescanType(Enum):
    ENVIRONMENT_LIGHTING = "Environment - Lighting",
    ENVIRONMENT_ARTEFACTS = "Environment - Artefacts",
    CARD_IN_SLAB_SLEEVE = "Card in Slab/Sleeve",
    CARD_OBSTRUCTION = "Card - Obstruction",
    CARD_ARTIFACTS = "CARD-ARTIFACTS",
    SCAN_PROCESS_FAILURE = "Scan Process Failure"


class GradingType(IntEnum):
    COLLECTION_2024 = 0
    COLLECTION = 1
    ADDED = 2
    SOLD = 3
    INSTANT = 4
    CARD_CENTERING = 6


class InstantGradeType(IntEnum):
    OVERALL = 0
    SUBGRADES = 1
    OVERALL_TO_SUBGRADES = 2


class GradingField(Enum):
    GRADING = "grading"
    CENTER  = "centering_grading"
    SURFACE = "surface_grading"
    EDGE    = "edge_grading"
    CORNER  = "corner_grading"
    ENVIRONMENT = "grading_environment"
    CONFIDENCE = "grading_confidence"
    STRUCTURE = "card_structure"


class CardType(Enum):
    POKEMON = "pokemon"
    LORCANA = "lorcana"
    MAGIC = "magic"
    YUGIOH = "yugioh"
    VIDEO_GAMES = "video_games"
    DIGIMON = "digimon"
    DRAGON_BALL = "dragon_ball"
    ONE_PIECE = "one_piece"


class GradingService(Enum):
    XIMILAR = "ximilar"
    OPENAI = "openai"
