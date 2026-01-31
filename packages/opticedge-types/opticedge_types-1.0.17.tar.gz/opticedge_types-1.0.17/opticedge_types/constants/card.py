from opticedge_types.enums.card import GradingType

ON_DEMAND_ELIGIBLE_GRADING_TYPES = {
    GradingType.COLLECTION_2024,
    GradingType.COLLECTION,
    GradingType.INSTANT,
}

POST_GRADING_ELIGIBLE_GRADING_TYPES = {
    GradingType.COLLECTION,
    GradingType.INSTANT,
}
