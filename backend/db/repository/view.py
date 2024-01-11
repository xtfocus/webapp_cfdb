from typing import List, Optional, Union

from db.models.table import TableName
from db.session import knowledgebase_engine as engine
from schemas.table import TableModel
from sqlalchemy import Date, MetaData, Table, and_, cast, func, select
from sqlalchemy.engine.base import Connection
from sqlalchemy.engine.row import Row
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import Session

metadata = MetaData()
# Loading the database as global vars
dictionary_table = Table(TableName.TRANSLATION.value, metadata, autoload_with=engine)
vn_synonym_table = Table(TableName.VN_SYNONYM.value, metadata, autoload_with=engine)

en_vsrc_tables = [
    Table(TableName.EN_DO.value, metadata, autoload_with=engine),
    Table(TableName.EN_UMLS.value, metadata, autoload_with=engine),
]

en_vsrc_synonym_tables = [
    Table(TableName.DO_SYNONYM.value, metadata, autoload_with=engine),
    Table(TableName.UMLS_SYNONYM.value, metadata, autoload_with=engine),
]

editor_table = Table(TableName.EDITOR.value, metadata, autoload_with=engine)


def get_count(db: Session, table: Table) -> int:
    """
    Count the number of rows in the given table.

    Parameters
    ----------
    db : Session
        SQLAlchemy Session.
    table : Table
        SQLAlchemy Table object.

    Returns
    -------
    int
        Number of rows in the table.
    """
    return db.query(table).count()


def get_table(table_name) -> Table:
    """
    Given the table name, return the SQLAlchemy Table object.

    Parameters
    ----------
    table_name : str
        Name of the table.
    metadata : MetaData
        SQLAlchemy MetaData object.
    engine : Engine
        SQLAlchemy Engine object.

    Returns
    -------
    Table
        SQLAlchemy Table object.
    """
    return Table(table_name, metadata, autoload_with=engine)


def get_table_summary(db: Session, table: Table) -> TableModel:
    """
    Given the table, return the TableModel object.

    Parameters
    ----------
    db : Session
        SQLAlchemy Session.
    table : Table
        SQLAlchemy Table object.
    engine : Engine
        SQLAlchemy Engine object.

    Returns
    -------
    TableModel
        Instance of the TableModel representing the table summary.
    """

    name = table.name
    n_rows = get_count(db, table)
    columns = list(table.columns.keys())

    inspector = inspect(engine)

    primary_key = [key.name for key in table.primary_key]

    foreign_key = inspector.get_foreign_keys(table.name)
    columns = inspector.get_columns(table.name)

    return {
        "name": name,
        "n_rows": n_rows,
        "columns": columns,
        "primary_key": primary_key,
        "foreign_key": foreign_key,
        "columns": columns,
    }


def locate_vn_term(term: str) -> Union[None, str, str, List[str], List[str]]:
    """
    Locate the Vietnamese term in the database.

    Parameters
    ----------
    term : str
        Vietnamese term to locate.

    Returns
    -------
    Union[None, str, str, List[str], List[str]]
        Tuple containing Vietnamese main, English main, Vietnamese synonyms, and English synonyms.
    """

    with engine.connect() as conn:
        # Search in tungdev_DICTIONARY for a match
        dictionary_match = vn_main_in_dictionary(conn, term)

        if dictionary_match:
            vn_main = dictionary_match.VN_main
            en_main = dictionary_match.EN_main
        else:
            # If not found in tungdev_DICTIONARY, search in tungdev_VN_SYNONYM
            vn_main = vn_synonym_to_vn_main(conn, term)

            if vn_main:
                en_main = vn_main_in_dictionary(conn, vn_main).EN_main

            else:
                # If no matches found for vn_main
                return None, None, None, None, None

        vn_synonyms = vn_main_to_synonyms(conn, vn_synonym_table, vn_main)
        en_synonyms = en_main_to_synonyms(
            conn, en_vsrc_tables, en_vsrc_synonym_tables, en_main
        )
        en_main_vsrc = {
            vsource.name: en_main_to_vsource_id(conn, vsource, en_main)
            for vsource in en_vsrc_tables
        }

        return vn_main, en_main, vn_synonyms, en_synonyms, en_main_vsrc


def vn_synonym_to_vn_main(conn: Connection, vn_term: str) -> Union[str, None]:
    """
    Given a vn_synonym, find its vn_main.
    Return None if not found
    """
    query_synonym = select(vn_synonym_table.c.VN_main).where(
        vn_synonym_table.c.VN_synonym == vn_term
    )
    result_main = conn.execute(query_synonym).fetchone()

    if result_main:
        vn_main = result_main.VN_main
        return vn_main
    else:
        return None


def vn_main_in_dictionary(conn: Connection, vn_main: str) -> Row:
    """
    Assuming vn_main 1:1 en_main. Find rows in
    dictionary_table where vn_main lies
    """
    match = conn.execute(
        select(dictionary_table).where(dictionary_table.c.VN_main == vn_main)
    ).fetchone()
    return match


def en_main_in_dictionary(conn: Connection, en_main: str) -> Row:
    """
    Assuming vn_main 1:1 en_main. Find rows in
    dictionary_table where en_main lies
    """
    match = conn.execute(
        select(dictionary_table).where(dictionary_table.c.EN_main == en_main)
    ).fetchone()
    return match


def vn_main_to_synonyms(
    conn: Connection, vn_synonym_table: Table, vn_main: str
) -> List[str]:
    """
    Assuming vn_main 1:1 en_main. Find rows in
    dictionary_table where vn_main lies
    """

    match = conn.execute(
        select(vn_synonym_table.c.VN_synonym).where(
            vn_synonym_table.c.VN_main == vn_main
        )
    ).fetchall()
    if not match:
        return []
    else:
        return [i.VN_synonym for i in match]


def en_main_to_vsource_id(conn: Connection, en_vsrc_table: Table, en_main: str) -> str:
    """
    Given a term assumed to be an en_main, find its mapping
        to validation source  en_vsrc_table

    If not found, return None
    """
    primary_key = [i.name for i in en_vsrc_table.primary_key.columns.values()][0]

    en_vsrc_match = conn.execute(
        select(en_vsrc_table.c[primary_key]).where(en_vsrc_table.c.EN_main == en_main)
    ).fetchone()

    if en_vsrc_match:
        return en_vsrc_match[0]
    else:
        return None


def en_main_to_synonyms(
    conn: Connection,
    en_vsrc_tables: List[Table],
    en_vsrc_synonym_tables: List[Table],
    en_main: str,
) -> List[str]:
    """
    Given en_main, find its synonym list
    """
    return_list = []

    for src, src_synonym in zip(en_vsrc_tables, en_vsrc_synonym_tables):
        primary_key = [i.name for i in src.primary_key.columns.values()][0]
        src_match = en_main_to_vsource_id(conn, src, en_main)

        if not src_match:
            continue

        synonym_match = conn.execute(
            select(src_synonym.c.EN_synonym).where(
                src_synonym.c[primary_key] == src_match
            )
        ).fetchall()
        if synonym_match:
            synonym_match = [i[0] for i in synonym_match]
        else:
            continue

        return_list += synonym_match
    return return_list


def en_synonym_to_vsource(
    conn: Connection, src_synonym: Table, en_synonym: str
) -> Union[Row, None]:
    """
    Given a term, check if it is a synonym in src_synonym table
    If it is, return the corresponding row. Otherwise return None
    """
    match = conn.execute(
        select(src_synonym).where(src_synonym.c.EN_synonym == en_synonym)
    ).fetchone()

    if match:
        return match
    else:
        return None


def en_synonym_to_en_main(conn: Connection, en_synonym: Table) -> Union[str, None]:
    """
    Given a term, check if it is a synonym
    If it is, return the corresponding en_main. Otherwise return None
    """

    en_main = None
    for src, src_synonym in zip(en_vsrc_tables, en_vsrc_synonym_tables):
        primary_key = [i.name for i in src.primary_key.columns.values()][0]
        src_synonym_match = en_synonym_to_vsource(conn, src_synonym, en_synonym)
        if src_synonym_match:
            src_code = src_synonym_match._asdict()[primary_key]

            en_main = (
                conn.execute(
                    select(src.c.EN_main).where(src.c[primary_key] == src_code)
                )
                .fetchone()
                .EN_main
            )
            return en_main
    return en_main


def locate_en_term(en_term: str) -> Union[None, str, str, List[str], List[str]]:
    """
    Locate the English term in the database.

    Parameters
    ----------
    en_term : str
        English term to locate.

    Returns
    -------
    Union[None, str, str, List[str], List[str]]
        Tuple containing Vietnamese main, English main, Vietnamese synonyms, and English synonyms.
    """

    with engine.connect() as conn:
        dictionary_match = en_main_in_dictionary(conn, en_term)

        if dictionary_match:
            en_main = dictionary_match.EN_main
            vn_main = dictionary_match.VN_main

        else:
            en_main = en_synonym_to_en_main(conn, en_term)
            if en_main:
                vn_main = en_main_in_dictionary(conn, en_main).VN_main
            else:
                return None, None, None, None, None

        vn_synonyms = vn_main_to_synonyms(conn, vn_synonym_table, vn_main)
        en_synonyms = en_main_to_synonyms(
            conn, en_vsrc_tables, en_vsrc_synonym_tables, en_main
        )

        en_main_vsrc = {
            vsource.name: en_main_to_vsource_id(conn, vsource, en_main)
            for vsource in en_vsrc_tables
        }

        return vn_main, en_main, vn_synonyms, en_synonyms, en_main_vsrc


def calculate_validated_en_main(en_vsrc_tables: List[Table]) -> int:
    with engine.connect() as conn:
        subquery = select(dictionary_table.c.EN_main)

        for src in en_vsrc_tables:
            subquery = subquery.join(src, dictionary_table.c.EN_main == src.c.EN_main)

        result = conn.execute(subquery).fetchall()

        if result:
            result = [i[0] for i in result]
            return result
        else:
            return []


def calculate_non_validated_en_main(en_vsrc_tables: List[Table]) -> int:
    with engine.connect() as conn:
        subquery = select(dictionary_table.c.EN_main)

        # Use a loop to dynamically join tables
        for table in en_vsrc_tables:
            subquery = subquery.outerjoin(
                table, dictionary_table.c.EN_main == table.c.EN_main
            )

        subquery = subquery.filter(
            and_(*[(table.c.EN_main == None) for table in en_vsrc_tables])
        )

        result = conn.execute(subquery).fetchall()

        if result:
            result = [i[0] for i in result]
            return result
        else:
            return []


def validated_en_main_statistics(en_vsrc_tables: List[Table]):
    """
    Count the number of en_main in dictionary table that are:
        - mapped to each validation source
        - mapped to all
        - mapped to none
    """
    result = dict()

    with engine.connect() as conn:
        result["dictionary_size"] = len(
            conn.execute(select(dictionary_table.c.EN_main)).fetchall()
        )

    result["count_uncharted_en_mains"] = len(
        calculate_non_validated_en_main(en_vsrc_tables)
    )
    result["count_charted"] = dict()
    for table in en_vsrc_tables:
        result["count_charted"][table.name] = len(calculate_validated_en_main([table]))

    result["count_charted_to_all_vsources"] = len(
        calculate_validated_en_main(en_vsrc_tables)
    )

    return result


def rows_per_editors(mode: str):
    f"""
    Count the number of {mode} rows per editor across all tables
    """
    if mode == "insert":
        user_col = "Insert_User"
    else:
        user_col = "Update_User"

    tables = (
        [dictionary_table, vn_synonym_table] + en_vsrc_tables + en_vsrc_synonym_tables
    )

    contribution = dict()
    with engine.connect() as conn:
        for table in tables:
            subquery = (
                select(
                    editor_table.c.User_Name,
                    func.count().label("n_rows"),
                )
                .select_from(
                    editor_table.outerjoin(
                        table,
                        editor_table.c.User_Id == table.c[user_col],
                    )
                )
                .group_by(editor_table.c.User_Id, editor_table.c.User_Name)
            )

            result = conn.execute(subquery)
            rows = result.fetchall()
            contribution[table.name] = dict(rows)

        return contribution


def standard_to_en_main(stdid: str, en_vsrc_table: Table, conn: Connection):
    primary_key = [key.name for key in en_vsrc_table.primary_key][0]
    query = select(en_vsrc_table.c.EN_main).where(en_vsrc_table.c[primary_key] == stdid)
    match = conn.execute(query).fetchone()
    return match


def standard_to_en_main_optional_source(stdid: str, en_vsrc_table: Optional[Table]):
    with engine.connect() as conn:
        if en_vsrc_table:
            match = standard_to_en_main(stdid, en_vsrc_table, conn)
            return match
        else:
            primary_keys = [
                [key.name for key in en_vsrc_table.primary_key][0]
                for en_vsrc_table in en_vsrc_tables
            ]
            for primary_key, en_vsrc_table in zip(primary_keys, en_vsrc_tables):
                match = standard_to_en_main(stdid, en_vsrc_table, conn)
                if match:
                    return match


def locate_standard(stdid: str, en_vsrc_table: Optional[Table]):
    en_main = standard_to_en_main_optional_source(stdid, en_vsrc_table)
    if en_main:
        en_main = en_main[0]
        with engine.connect() as conn:
            en_synonyms = en_main_to_synonyms(
                conn, en_vsrc_tables, en_vsrc_synonym_tables, en_main
            )
            vn_main = en_main_in_dictionary(conn, en_main).VN_main
            vn_synonyms = vn_main_to_synonyms(conn, vn_synonym_table, vn_main)
            en_main_vsrc = {
                vsource.name: en_main_to_vsource_id(conn, vsource, en_main)
                for vsource in en_vsrc_tables
            }

            return vn_main, en_main, vn_synonyms, en_synonyms, en_main_vsrc


def review_per_day(table: Table, date: str = None, mode="update"):
    """
    Show daily records from table
    table: sqlalchemy.Table
    date: YMD format, e.g., "2023-12-31"
    mode: insert or update. If Update, filter where Update_Date == date, etc
    """
    with engine.connect() as conn:
        if not date:
            # If date is not provided, get the latest date from the table
            latest_date_query = select(func.max(table.c.Update_Date))
            result = conn.execute(latest_date_query)
            latest_date = result.scalar()
            date = latest_date.strftime("%Y-%m-%d") if latest_date else None

        if mode != "update":
            query = select(table).where(cast(table.c.Insert_Date, Date) == date)
        else:
            query = select(table).where(cast(table.c.Update_Date, Date) == date)
        result = conn.execute(query)
        records = result.fetchall()

        # Convert records to a dictionary with column names
        # as keys and lists as values
        columns_data = {col: [] for col in result.keys()}
        for record in records:
            for col, value in zip(result.keys(), record):
                columns_data[col].append(value)

        return columns_data
