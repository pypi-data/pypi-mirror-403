import pandas as pd

def build_incident_dataframes(
    df: pd.DataFrame,
    extracted_col: str = "extracted_at",
    id_col: str = "situation_id",
    end_col: str = "situation_record_end_time",
    status_col: str = "validity_status",
    active_value: str = "active",
    inactive_value: str = "inactive",
):
    # Copy to avoid side-effects
    df = df.copy()

    # Ensure datetime + sort
    df[extracted_col] = pd.to_datetime(df[extracted_col], errors="coerce")
    df = df.dropna(subset=[extracted_col, id_col]).sort_values(extracted_col)

    # Unique extracted_at timestamps (sorted)
    timestamps = df[extracted_col].drop_duplicates().tolist()

    # We'll build one-row-per-incident table
    incidents_by_id = {}  # situation_id -> row (as Series / dict)

    prev_ids = set()

    for ts in timestamps:
        # IDs present at this timestamp
        cur_ids = set(df.loc[df[extracted_col] == ts, id_col].unique())

        # 1) Close incidents that disappeared (prev but not current)
        closed_ids = prev_ids - cur_ids
        for sid in closed_ids:
            if sid in incidents_by_id:
                incidents_by_id[sid][end_col] = ts
                incidents_by_id[sid][status_col] = inactive_value

        # 2) Create incidents that are new (current but not prev)
        new_ids = cur_ids - prev_ids
        if new_ids:
            # Pick ONE representative row per new situation_id at this timestamp
            # (If you have multiple rows per id in the same ts, we take the first one.)
            rows_new = (
                df.loc[(df[extracted_col] == ts) & (df[id_col].isin(new_ids))]
                .sort_values([id_col])  # stable order
                .drop_duplicates(subset=[id_col], keep="first")
            )

            for _, row in rows_new.iterrows():
                sid = row[id_col]
                record = row.to_dict()

                # Ensure end/status columns exist
                record[end_col] = pd.NaT
                record[status_col] = active_value

                incidents_by_id[sid] = record

        # 3) Continuing incidents: do nothing
        prev_ids = cur_ids

    # Build final table (one row per incident)
    incidents_table = pd.DataFrame(list(incidents_by_id.values()))

    incidents_table = incidents_table.sort_values("situation_record_creation_time", ascending=True)

    return incidents_table