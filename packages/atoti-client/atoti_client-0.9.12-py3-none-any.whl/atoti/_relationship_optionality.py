from typing import Literal

from ._graphql import RelationshipOptionality as _GraphQlRelationshipOptionality

RelationshipOptionality = Literal["mandatory", "optional"]


def relationship_optionality_to_graphql(
    relationship_optionality: RelationshipOptionality,
    /,
) -> _GraphQlRelationshipOptionality:
    match relationship_optionality:
        case "mandatory":
            return _GraphQlRelationshipOptionality.MANDATORY
        case "optional":  # pragma: no branch (avoid `case _` to detect new variants)
            return _GraphQlRelationshipOptionality.OPTIONAL
