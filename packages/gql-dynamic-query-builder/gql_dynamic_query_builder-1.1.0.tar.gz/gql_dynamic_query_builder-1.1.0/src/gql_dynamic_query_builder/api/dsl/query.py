from gql_dynamic_query_builder.api.builder import GQLDynamicQueryBuilder
from gql_dynamic_query_builder.api.dsl.building_blocks.query_block import QueryBuildingBlock


def dynamic_query(query: str) -> QueryBuildingBlock:
    builder = GQLDynamicQueryBuilder(query)
    return QueryBuildingBlock(builder)