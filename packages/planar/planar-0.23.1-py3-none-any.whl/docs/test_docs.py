# -*- coding: utf-8 -*-
import asyncio
from pathlib import Path

import pytest
from sqlalchemy.exc import DBAPIError
from sqlmodel import col, delete, insert, select, update
from xdoctest.core import parse_docstr_examples

from planar.db import DatabaseManager, new_session


def doctest_setup_namespace(namespace, db_url):
    # Inject necessary items into the global namespace for xdoctest
    # This allows the doctests in the docstring to access these variables/functions
    # Models and session are now defined/created within the doctest itself.
    namespace["new_session"] = new_session
    namespace["DatabaseManager"] = DatabaseManager
    namespace["db_url"] = db_url
    namespace["asyncio"] = asyncio
    namespace["select"] = select
    namespace["insert"] = insert
    namespace["update"] = update
    namespace["delete"] = delete
    namespace["col"] = col
    namespace["DBAPIError"] = DBAPIError
    namespace["ValueError"] = ValueError


# @pytest.mark.skip()
@pytest.mark.parametrize(
    "doc_file",
    ["sqlalchemy_usage.md", "entities.md"],
    ids=["sqlalchemy_usage", "entities"],
)
def test_sqlalchemy_usage_docs(tmp_sqlite_url: str, doc_file: str):
    # Configure xdoctest:
    # 'google' style recognizes ```python blocks.
    # '+REPORT_NDIFF' gives better diffs on failure.
    # '+IGNORE_EXCEPTION_DETAIL' can hide verbose tracebacks for expected exceptions.
    # '+NORMALIZE_WHITESPACE' helps with minor formatting differences.
    config = {
        "style": "google",
        "options": "+REPORT_NDIFF +NORMALIZE_WHITESPACE",
    }

    current_dir = Path(__file__).parent
    f = current_dir / doc_file
    doctest_str = f.read_text()
    doctests = parse_docstr_examples(doctest_str, callname=f.name)
    print(doctests)

    for doctest in doctests:
        print(doctest)
        # Setup namespace for each doctest run
        # Session is now created *inside* the doctest markdown
        doctest_setup_namespace(doctest.global_namespace, tmp_sqlite_url)
        doctest.config.update(config)
        doctest.run(verbose=2)
