from datetime import datetime, timedelta
from typing import Optional

import matplotlib.pyplot as plt
from db.repository.view import (dictionary_table, editor_table,
                                en_vsrc_synonym_tables, en_vsrc_tables, engine,
                                vn_synonym_table)
from pydantic import BaseModel, validator
from sqlalchemy import Date, Table, cast, column, func, select


class DateModel(BaseModel):
    date_str: str

    @validator("date_str")
    def validate_date_format(cls, value):
        try:
            # Use strptime to parse the input string with the specified format
            datetime.strptime(value, "%d/%m/%Y")
        except ValueError:
            raise ValueError("Invalid date format. Please use dd/mm/yyyy.")

        return value


def editor_activity(
    from_date: Optional[DateModel] = None, to_date: Optional[DateModel] = None
):
    """
    Editor activity count (based on update_date) each day for across tables (not aggregated)
    """
    tables = (
        [dictionary_table, vn_synonym_table] + en_vsrc_tables + en_vsrc_synonym_tables
    )

    dfs = []
    for table in tables:
        try:
            df = editor_activity_per_table(table, from_date, to_date)
            dfs.append(df)
        except ValueError:
            dfs.append([])
    return dict(zip([table.name for table in tables], dfs))


def editor_activity_per_table(
    table: Table, from_date: Optional[datetime], to_date: Optional[datetime]
):
    """
    Acitivity of each editor for `table` from from_date to `to_date`
    """
    with engine.connect() as conn:
        if not from_date:
            from_date = conn.execute(select(func.min(table.c.Update_Date))).scalar()
        if not to_date:
            to_date = conn.execute(select(func.max(table.c.Update_Date))).scalar()

    try:
        assert to_date >= from_date
    except AssertionError:
        raise ValueError("from_date must be smaller than to_date")

    user_col = "Update_User"

    with engine.connect() as conn:
        date_col = table.c.Update_Date

        temp_table = (
            select(
                table.c[user_col].label("user_col"),
                cast(table.c["Update_Date"], Date).label("Just_Date"),
                func.count().label("activity"),
            )
            .filter((date_col <= to_date) & (date_col >= from_date))
            .group_by(table.c[user_col], cast(table.c["Update_Date"], Date))
        )

        temp_alias = temp_table.alias()

        # Get editor name
        query = select(
            editor_table.c.User_Name, column("Just_Date"), column("activity")
        ).select_from(
            temp_alias.join(
                editor_table, temp_alias.c.user_col == editor_table.c.User_Id
            )
        )

        df = conn.execute(query).fetchall()

        df = [(a, b.strftime("%Y-%m-%d"), c) for (a, b, c) in df]

        # Extract unique user IDs
        editor_ids = set(item[0] for item in df)
        # Organize data into dictionaries for each user
        editor_data = {
            editor_id: {"dates": [], "activity": []} for editor_id in editor_ids
        }

        for editor_id, date, activity in df:
            editor_data[editor_id]["dates"].append(date)
            editor_data[editor_id]["activity"].append(activity)

        for editor_id in editor_ids:
            editor_data[editor_id] = fill_missing_dates(
                from_date, to_date, editor_data[editor_id]
            )

        return editor_data


def fill_missing_dates(start_date, end_date, user_info):
    # Create a set of existing dates
    existing_dates = set(
        datetime.strptime(date, "%Y-%m-%d") for date in user_info["dates"]
    )

    # Generate a list of consecutive dates within the specified range
    all_dates = [
        start_date + timedelta(days=x) for x in range((end_date - start_date).days + 1)
    ]

    # Fill in missing dates with activity 0
    for date in all_dates:
        date_str = date.strftime("%Y-%m-%d")
        if date not in existing_dates:
            user_info["dates"].append(date_str)
            user_info["activity"].append(0)

    # Sort the data based on dates
    sorted_data = sorted(zip(user_info["dates"], user_info["activity"]))
    user_info["dates"], user_info["activity"] = zip(*sorted_data)

    return user_info


def create_activity_chart(data, table_name, save_to):
    # Create a figure and axes
    fig, ax = plt.subplots(figsize=(10, 6))

    # Plotting on the axes
    for editor_id, user_info in data.items():
        ax.plot(
            user_info["dates"],
            user_info["activity"],
            label=f"User {editor_id}",
            alpha=0.6,
        )
        print(user_info)
        print()

    ax.set_xlabel("Date")
    ax.set_ylabel("Activity")
    ax.set_title(f"User Activity {table_name}")
    ax.tick_params(axis="x", rotation=45)
    ax.legend()

    # Save the plot to a PNG file
    fig.savefig(save_to)
