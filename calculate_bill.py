import pandas as pd

def calculate_bills():
    STD_RATE_LT = 140.0
    DEMAND_RATE_LT = 190.0
    STD_RATE_HT = 250.0
    DEMAND_RATE_HT = 300.0
    
    ENERGY_CHARGE_RATE = 6.10
    PENALTY_MULTIPLIER = 2.0
    
    df = pd.read_csv('factory_load_data.csv', parse_dates=['Timestamp'])
    df['Hour'] = df['Timestamp'].dt.hour
    df['Date'] = df['Timestamp'].dt.date
    
    def get_tod_rate(hour):
        if (6 <= hour < 9) or (18 <= hour < 22):
            return ENERGY_CHARGE_RATE + 1.00
        elif (22 <= hour) or (0 <= hour < 6):
            return max(0, ENERGY_CHARGE_RATE - 1.00)
        return ENERGY_CHARGE_RATE

    df['ToD_Rate'] = df['Hour'].apply(get_tod_rate)
    
    cases = ['Case_1_kW', 'Case_2_kW', 'Case_3_kW', 'Case_4_kW']
    sanctioned_loads = range(60, 121, 10)
    
    summary_demand = []
    summary_standard = []
    daily_results = []

    for case in cases:
        df[f'{case}_kWh'] = df[case] * 0.25
        df[f'{case}_Cost'] = df[f'{case}_kWh'] * df['ToD_Rate']
        
        max_demand = df[case].max()
        total_kwh = df[f'{case}_kWh'].sum()
        total_energy_cost = df[f'{case}_Cost'].sum()
        
        # Calculate Blended Daily ToD Effective Rate
        daily_group = df.groupby('Date').agg({
            case: 'max', 
            f'{case}_kWh': 'sum',
            f'{case}_Cost': 'sum'
        }).reset_index()
        
        for _, row in daily_group.iterrows():
            d_kwh = row[f'{case}_kWh']
            d_cost = row[f'{case}_Cost']
            eff_rate = d_cost / d_kwh if d_kwh > 0 else 0
            daily_results.append({
                'Case': case, 
                'Date': row['Date'], 
                'Daily_Max_kW': round(row[case], 2),
                'Daily_Effective_Rate': round(eff_rate, 2)
            })

        for sl in sanctioned_loads:
            std_rate = STD_RATE_HT if sl >= 75 else STD_RATE_LT
            dem_rate = DEMAND_RATE_HT if sl >= 75 else DEMAND_RATE_LT
            
            # Standard Billing
            base_std_fixed = sl * std_rate
            penalty_std = max(0, max_demand - sl) * (std_rate * PENALTY_MULTIPLIER)
            total_std_bill = base_std_fixed + penalty_std + total_energy_cost
            
            summary_standard.append({
                'Case': case, 'Sanctioned_Load_kW': sl, 'Max_Demand_kW': round(max_demand, 2),
                'Base_Fixed_Charge_Rs': round(base_std_fixed, 2), 'Penalty_Charge_Rs': round(penalty_std, 2),
                'Total_Fixed_Charges_Rs': round(base_std_fixed + penalty_std, 2), 'Energy_Charge_Rs': round(total_energy_cost, 2),
                'Total_Bill_Rs': round(total_std_bill, 2)
            })

            # Demand Billing
            billing_demand = max(0.85 * sl, min(max_demand, sl))
            base_dem_fixed = billing_demand * dem_rate
            penalty_dem = max(0, max_demand - sl) * (dem_rate * PENALTY_MULTIPLIER)
            total_dem_bill = base_dem_fixed + penalty_dem + total_energy_cost
            
            summary_demand.append({
                'Case': case, 'Sanctioned_Load_kW': sl, 'Max_Demand_kW': round(max_demand, 2),
                'Base_Demand_Charge_Rs': round(base_dem_fixed, 2), 'Penalty_Charge_Rs': round(penalty_dem, 2),
                'Total_Demand_Charges_Rs': round(base_dem_fixed + penalty_dem, 2), 'Energy_Charge_Rs': round(total_energy_cost, 2),
                'Total_Bill_Rs': round(total_dem_bill, 2)
            })

    pd.DataFrame(summary_standard).to_csv('billing_summary_standard.csv', index=False)
    pd.DataFrame(summary_demand).to_csv('billing_summary_demand.csv', index=False)
    pd.DataFrame(daily_results).to_csv('daily_profile.csv', index=False)
    print("Generated billing summaries and updated daily profile.")

if __name__ == "__main__":
    calculate_bills()