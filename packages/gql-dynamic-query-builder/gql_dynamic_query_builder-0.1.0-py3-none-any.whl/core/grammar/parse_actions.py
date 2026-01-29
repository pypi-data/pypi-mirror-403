### These functions are used as parse actions for matches
from pyparsing import ParseResults


def extend_where_clauses(
    existing_where_clause: ParseResults, where_clauses: str
) -> str:
    return ' ' + ''.join(existing_where_clause) + ''.join(where_clauses) + ' '


def inject_new_where_clauses(where_clauses) -> str:
    return ' where: {' + ''.join(where_clauses) + '} '


def create_filter_section_with_where_clauses(where_clauses) -> str:
    return '(where: {' + ''.join(where_clauses) + '})'
