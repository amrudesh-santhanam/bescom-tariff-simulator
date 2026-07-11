import sqlite3
from pathlib import Path

import pandas as pd

DB_PATH = Path(__file__).resolve().parent / 'data.db'


def get_connection():
    return sqlite3.connect(DB_PATH)


def ensure_database_schema(conn):
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS session_state (
            current_session_id INTEGER NOT NULL
        )
        """
    )
    conn.execute(
        "INSERT OR IGNORE INTO session_state (current_session_id) VALUES (1)"
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS factory_load_data (
            session_id INTEGER NOT NULL,
            Timestamp TEXT NOT NULL,
            Case_1_kW REAL,
            Case_2_kW REAL,
            Case_3_kW REAL,
            Case_4_kW REAL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS daily_energy_consumption (
            session_id INTEGER NOT NULL,
            Date TEXT NOT NULL,
            Case_1_kWh REAL,
            Case_2_kWh REAL,
            Case_3_kWh REAL,
            Case_4_kWh REAL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS billing_summary_standard (
            session_id INTEGER NOT NULL,
            case_name TEXT NOT NULL,
            Sanctioned_Load_kW REAL,
            Max_Demand_kW REAL,
            Base_Fixed_Charge_Rs REAL,
            Penalty_Charge_Rs REAL,
            Total_Fixed_Charges_Rs REAL,
            Energy_Charge_Rs REAL,
            Total_Bill_Rs REAL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS billing_summary_demand (
            session_id INTEGER NOT NULL,
            case_name TEXT NOT NULL,
            Sanctioned_Load_kW REAL,
            Max_Demand_kW REAL,
            Base_Demand_Charge_Rs REAL,
            Penalty_Charge_Rs REAL,
            Total_Demand_Charges_Rs REAL,
            Energy_Charge_Rs REAL,
            Total_Bill_Rs REAL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS daily_profile (
            session_id INTEGER NOT NULL,
            case_name TEXT NOT NULL,
            Date TEXT NOT NULL,
            Daily_Max_kW REAL,
            Daily_Effective_Rate REAL
        )
        """
    )
    conn.commit()


def get_current_session_id(conn):
    query = "SELECT current_session_id FROM session_state LIMIT 1"
    result = pd.read_sql_query(query, conn)
    if result.empty:
        return 1
    return int(result.iloc[0]['current_session_id'])


def set_current_session_id(conn, session_id):
    conn.execute(
        "UPDATE session_state SET current_session_id = ?",
        (session_id,),
    )
    conn.commit()


def get_next_session_id(conn, table_name):
    query = f"SELECT COALESCE(MAX(session_id), 0) AS max_session_id FROM {table_name}"
    max_session_id = pd.read_sql_query(query, conn).iloc[0]['max_session_id']
    return int(max_session_id) + 1


def get_latest_session_id(conn, table_name='factory_load_data'):
    query = f"SELECT COALESCE(MAX(session_id), 0) AS latest_session_id FROM {table_name}"
    latest_session_id = pd.read_sql_query(query, conn).iloc[0]['latest_session_id']
    return int(latest_session_id)


def load_session_dataframe(conn, table_name, session_id):
    query = f"SELECT * FROM {table_name} WHERE session_id = ? ORDER BY Timestamp"
    return pd.read_sql_query(query, conn, params=(session_id,))


def save_dataframe_to_table(df, table_name, conn, session_id):
    table_df = df.copy()
    if 'Case' in table_df.columns and table_name in {'billing_summary_standard', 'billing_summary_demand', 'daily_profile'}:
        table_df = table_df.rename(columns={'Case': 'case_name'})
    table_df.insert(0, 'session_id', session_id)
    table_df.to_sql(table_name, conn, if_exists='append', index=False)
