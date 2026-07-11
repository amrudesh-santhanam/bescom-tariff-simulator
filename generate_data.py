import pandas as pd
import numpy as np
from datetime import timedelta

from sqlite_store import (
    DB_PATH,
    ensure_database_schema,
    get_connection,
    get_next_session_id,
    save_dataframe_to_table,
)


def generate_load_profile():
    days_in_month = 30
    interval_mins = 15
    periods_per_day = int((24 * 60) / interval_mins)
    total_periods = days_in_month * periods_per_day
    
    start_time = pd.Timestamp('2025-04-01 00:00:00')
    timestamps = [start_time + timedelta(minutes=i*interval_mins) for i in range(total_periods)]
    
    max_load = 105.0 
    base_sundry = 2.0 
    
    data = {'Timestamp': timestamps}
    
    def get_load(shift_active, target_load_pct):
        if not shift_active:
            return base_sundry + np.random.uniform(0, 1.5)
        target = max_load * target_load_pct
        noise = np.random.normal(0, target * 0.1) 
        return min(max(target + noise, base_sundry), max_load)

    # Case 1: Consistent High Orders (3 shifts all month)
    case1 = []
    for dt in timestamps:
        case1.append(get_load(shift_active=True, target_load_pct=0.95))
    data['Case_1_kW'] = case1

    # Case 2: Order low throughout the month (1 shift, 30% load)
    case2 = []
    for dt in timestamps:
        hour = dt.hour 
        shift_active = (6 <= hour < 14)
        case2.append(get_load(shift_active, 0.30))
    data['Case_2_kW'] = case2

    # Case 3: Low Orders + 2 day spike
    case3 = []
    for dt in timestamps:
        day = dt.day
        hour = dt.hour 
        if day in [14, 15]:
            shift_active = (6 <= hour < 22)
            case3.append(get_load(shift_active, 0.95))
        else:
            shift_active = (6 <= hour < 14)
            case3.append(get_load(shift_active, 0.30))
    data['Case_3_kW'] = case3

    # Case 4: 3 weeks max, 1 week holiday
    case4 = []
    for dt in timestamps:
        day = dt.day
        hour = dt.hour
        shift_active = False if day > 21 else (6 <= hour < 22)
        case4.append(get_load(shift_active, 0.95))
    data['Case_4_kW'] = case4

    df = pd.DataFrame(data)

    with get_connection() as conn:
        ensure_database_schema(conn)
        session_id = get_next_session_id(conn, 'factory_load_data')

        save_dataframe_to_table(df, 'factory_load_data', conn, session_id)

        daily_df = df.copy()
        daily_df['Date'] = daily_df['Timestamp'].dt.date
        daily_energy = daily_df.groupby('Date').agg({
            'Case_1_kW': lambda x: (x * 0.25).sum(),
            'Case_2_kW': lambda x: (x * 0.25).sum(),
            'Case_3_kW': lambda x: (x * 0.25).sum(),
            'Case_4_kW': lambda x: (x * 0.25).sum()
        }).reset_index()
        daily_energy.columns = ['Date', 'Case_1_kWh', 'Case_2_kWh', 'Case_3_kWh', 'Case_4_kWh']
        daily_energy.insert(0, 'session_id', session_id)
        daily_energy.to_sql('daily_energy_consumption', conn, if_exists='append', index=False)

    print(f"Generated and saved data to '{DB_PATH}' successfully with session_id={session_id}.")

if __name__ == "__main__":
    generate_load_profile()