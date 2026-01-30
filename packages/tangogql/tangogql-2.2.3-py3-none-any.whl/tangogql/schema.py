import os

from ariadne import load_schema_from_path, make_executable_schema

from . import mutation, query, subscription

type_defs = load_schema_from_path(os.path.dirname(__file__) + "/tangogql.graphql")


schema = make_executable_schema(
    type_defs, *query.types, *mutation.types, *subscription.types
)
