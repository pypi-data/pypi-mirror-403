from pyparsing import (
    Empty,
    Keyword,
    Literal,
    OneOrMore,
    Optional,
    ParserElement,
    Word,
    ZeroOrMore,
    alphas,
    original_text_for,
)

from src.core.grammar.parse_actions import (
    create_filter_section_with_where_clauses,
    extend_where_clauses,
    inject_new_where_clauses,
)
from src.core.grammar.subquery import GENERIC_SUBQUERY, get_table_specific_subquery
from src.core.grammar.where_clause import get_new_where_clause_and_content

QUERY_KEYWORD_AND_NAME = original_text_for(Literal('query') + Word(alphas + '_'))
QUERY_PARAMETER = Literal('$') + Word(alphas + '_') + Literal(':') + Word(alphas)
QUERY_PARAMETER_SECTION = Literal('(') + OneOrMore(QUERY_PARAMETER) + Literal(')')


def prepare_query_grammar(table_name: str, where_clauses: str) -> ParserElement:
    where_clause, recursive_where_condition = get_new_where_clause_and_content()
    no_where_clause = Empty()
    no_filters = Empty()

    table_subquery = get_table_specific_subquery(
        table_name, where_clause | no_where_clause, no_filters
    )
    other_subqueries = ~Keyword(table_name) + GENERIC_SUBQUERY.copy()

    recursive_where_condition.set_parse_action(
        lambda tokens: extend_where_clauses(tokens, where_clauses)
    )
    no_where_clause.set_parse_action(lambda: inject_new_where_clauses(where_clauses))
    no_filters.set_parse_action(
        lambda: create_filter_section_with_where_clauses(where_clauses)
    )

    return (
        QUERY_KEYWORD_AND_NAME.copy()
        + Optional(QUERY_PARAMETER_SECTION.copy())
        + Literal('{')
        + ZeroOrMore(other_subqueries)
        + table_subquery
        + ZeroOrMore(other_subqueries)
        + Literal('}')
    )
