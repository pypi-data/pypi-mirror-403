from __future__ import annotations

from gql_dynamic_query_builder.api.builder import GQLDynamicQueryBuilder


class QueryBuildingBlock:
    builder = None

    def __init__(self, builder: GQLDynamicQueryBuilder) -> None:
        self.builder = builder

    def finalize(self) -> GQLDynamicQueryBuilder:
        return self.builder

    def build(self) -> str:
        return self.builder.build()

    def table(
        self, table_name: str
    ) -> SubQueryBuildingBlock:
        return SubQueryBuildingBlock(self.builder, table_name)


class SubQueryBuildingBlock:
    def __init__(self, builder: GQLDynamicQueryBuilder, table_name: str) -> None:
        self.builder = builder
        self.table_name = table_name

    def where(self, field_name: str, is_optional: bool = False) -> WhereBuildingBlock:
        return WhereBuildingBlock(
            self.builder, self.table_name, field_name, is_optional
        )

    def opt_where(self, field_name: str) -> WhereBuildingBlock:
        return WhereBuildingBlock(self.builder, self.table_name, field_name, is_optional=False)

    def limit(self, limit: int) -> SubQueryBuildingBlock:
        self.builder = self.builder.with_limit(self.table_name, limit)
        return self

    def offset(self, offset: int) -> SubQueryBuildingBlock:
        self.builder = self.builder.with_offset(self.table_name, offset)
        return self

    def finalize(self) -> QueryBuildingBlock:
        return QueryBuildingBlock(self.builder)

    def build(self):
        return QueryBuildingBlock(self.builder).build()

    def table(
        self, table_name: str
    ) -> SubQueryBuildingBlock:
        return SubQueryBuildingBlock(self.builder, table_name)


class WhereBuildingBlock:
    def __init__(
        self,
        builder: GQLDynamicQueryBuilder,
        table_name: str,
        field_name: str,
        is_optional: bool,
    ) -> None:
        self.is_optional = is_optional
        self.builder = builder
        self.table_name = table_name
        self.field_name = field_name

    def _eq(self, value: str | float | int) -> SubQueryBuildingBlock:
        self.builder = self.builder.with_where_clause(
            self.table_name, self.field_name, value, '_eq', self.is_optional
        )
        return SubQueryBuildingBlock(self.builder, self.table_name)

    def _neq(self, value: str | float | int) -> SubQueryBuildingBlock:
        self.builder = self.builder.with_where_clause(
            self.table_name, self.field_name, value, '_neq', self.is_optional
        )
        return SubQueryBuildingBlock(self.builder, self.table_name)

    def _gt(self, value: str | float | int) -> SubQueryBuildingBlock:
        self.builder = self.builder.with_where_clause(
            self.table_name, self.field_name, value, '_gt', self.is_optional
        )
        return SubQueryBuildingBlock(self.builder, self.table_name)

    def _gte(self, value: str | float | int) -> SubQueryBuildingBlock:
        self.builder = self.builder.with_where_clause(
            self.table_name, self.field_name, value, '_gte', self.is_optional
        )
        return SubQueryBuildingBlock(self.builder, self.table_name)

    def _lt(self, value: str | float | int) -> SubQueryBuildingBlock:
        self.builder = self.builder.with_where_clause(
            self.table_name, self.field_name, value, '_lt', self.is_optional
        )
        return SubQueryBuildingBlock(self.builder, self.table_name)

    def _lte(self, value: str | float | int) -> SubQueryBuildingBlock:
        self.builder = self.builder.with_where_clause(
            self.table_name, self.field_name, value, '_lte', self.is_optional
        )
        return SubQueryBuildingBlock(self.builder, self.table_name)

    def _in(self, values: list) -> SubQueryBuildingBlock:
        self.builder = self.builder.with_where_clause(
            self.table_name, self.field_name, values, '_in', self.is_optional
        )
        return SubQueryBuildingBlock(self.builder, self.table_name)

    def _nin(self, values: list) -> SubQueryBuildingBlock:
        self.builder = self.builder.with_where_clause(
            self.table_name, self.field_name, values, '_nin', self.is_optional
        )
        return SubQueryBuildingBlock(self.builder, self.table_name)

    def _is_null(self, value: bool) -> SubQueryBuildingBlock:
        self.builder = self.builder.with_where_clause(
            self.table_name, self.field_name, value, '_is_null', self.is_optional
        )
        return SubQueryBuildingBlock(self.builder, self.table_name)
