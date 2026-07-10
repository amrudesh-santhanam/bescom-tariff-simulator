# BESCOM LT-5 Factory Tariff & BESS Simulator

This toolkit provides a complete simulation environment to understand how factory electricity bills are calculated under Karnataka's BESCOM LT-5 tariff. It generates synthetic 15-minute interval power load data, applies standard and demand-based tariff rules (including Time of Day pricing), tracks energy consumption, and visualizes the results in an interactive dashboard.

---

## 📂 File Overview

### 1. `generate_data.py`
* **Purpose:** Generates synthetic power usage data for a 30-day month at 15-minute intervals.
* **Outputs:** * `factory_load_data.csv` (Raw 15-min kW profiles)
  * `daily_energy_consumption.csv` (Aggregated daily kWh usage)
* **Scenarios Simulated:**
  * **Case 1:** Consistent High Orders (3 shifts running at 95% load all month).
  * **Case 2:** Low Orders (1 shift running at 30% load).
  * **Case 3:** Low Orders + 2-Day Spike (Mostly 1 shift, but a sudden 2-day burst of max load).
  * **Case 4:** 3 Weeks Max Load, 1 Week Holiday (Factory shuts down in the last week).

### 2. `calculate_bill.py`
* **Purpose:** Reads the generated load data and applies BESCOM LT-5 billing logic to calculate monthly costs across varying Sanctioned Loads (60kW to 120kW).
* **Outputs:** * `billing_summary_standard.csv` (Standard billing without demand option)
  * `billing_summary_demand.csv` (Demand-Based billing option)
  * `daily_profile.csv` (Daily maximum demand and effective per-kWh rate)

### 3. `index.html`
* **Purpose:** An interactive, browser-based dashboard to visualize the generated CSV data.
* **Features:** Upload the four output CSVs to view side-by-side comparisons of total bills, isolated penalty charges, daily peak demand spikes, effective Time of Day (ToD) rates, and daily energy consumption.

---

## 🚀 Execution Steps

### Prerequisites
Make sure you have Python installed, along with the `pandas` and `numpy` libraries.
`pip install pandas numpy`

### Step-by-Step Guide
1. **Generate the Load Profile:**
   Run the data generator script to create the raw synthetic data and energy files.
   `python generate_data.py`

2. **Calculate the Bills:**
   Run the tariff calculator to process the load data and generate the billing summaries.
   `python calculate_bill.py`

3. **View the Dashboard:**
   * Double-click `index.html` to open it in any modern web browser (Chrome, Edge, Safari, Firefox).
   * Click the upload buttons at the top of the page to load all four CSVs generated in the previous steps.
   * Use the dropdown menu to toggle between the 4 different factory order cases and analyze the charts.

---

## 💡 Key Observations & Clarifications

While analyzing the data in the dashboard, you may notice two specific behaviors. Here is the mathematical explanation for why they happen under BESCOM rules:

### 1. Why is there little to no difference between Standard and Demand-Based billing in some cases?
You will notice in **Cases 1, 3, and 4** that the Standard Bill and the Demand-Based Bill are often identical. This happens when your **Maximum Demand (MD)** exceeds your **Sanctioned Load (SL)**.

* **Standard Tariff:** Always bills you for 100% of your Sanctioned Load. 
* **Demand Tariff:** Bills you for *either* 85% of your Sanctioned Load *or* your recorded Max Demand, **whichever is higher** (capped at the Sanctioned Load limit). 

> **Example:** If your factory pulls 105kW (MD) and your Sanctioned Load is 80kW, your MD is higher than your SL. Both tariffs cap the base billing at 100% of the Sanctioned Load (80kW) and apply the exact same 2x penalty to the excess 25kW. 

**When is Demand-Based useful?** You only see savings from Demand-Based billing in **Case 2**, where the MD (~35kW) is significantly lower than the Sanctioned Load. This allows the demand bill to drop down to the 85% minimum threshold, whereas the Standard tariff forces you to pay for the full 100%.

### 2. Why doesn't the final bill change much when I increase my Sanctioned Load?
When looking at the Overall Monthly Bill Comparison for **Cases 1, 3, and 4**, the total bill seems relatively flat whether you choose 60kW or 120kW. This is a matter of **scale**.

* **High Usage (Cases 1, 3, 4):** The cost of the actual energy consumed (kWh × ~Rs. 6.10) dominates the bill, often running into lakhs of rupees per month. Even though heavy 2x penalties are being applied for exceeding a 60kW sanctioned load, a penalty of Rs. 20,000 is a tiny fraction of a Rs. 4,500,000 energy bill. The total bill barely moves percentage-wise. *(To see the penalties clearly, refer to Chart 2: Penalty Breakdown in the dashboard).*
* **Low Usage (Case 2):** Because the factory is running at 30% load for only one shift, the energy usage drops drastically. Without massive energy costs overshadowing the fixed charges, changes to the Sanctioned Load (and the corresponding fixed/demand capacity fees) become highly visible on the total bill chart.

---

## 🔋 Cost Optimization using BESS & Diesel Generators

For factories facing strict BESCOM LT-5 penalties and Time of Day (ToD) rules, a **Battery Energy Storage System (BESS)**, especially paired with a Diesel Generator (DG), can drastically cut operational expenses.

### 1. Peak Shaving (Avoiding 2x Penalties)
Under the LT-5 demand-based tariff, exceeding Sanctioned Load triggers a 2x penalty on the excess load. If your sanctioned load is 75kW, but your factory occasionally spikes to 105kW (as seen in our simulations), you pay heavily for that 30kW spike. 
* **The BESS Solution:** A BESS can be programmed with a strict grid limit. During a 105kW spike, it instantly discharges 30kW from the battery. The grid only "sees" 75kW, entirely dodging the massive demand penalties.

### 2. Energy Arbitrage (ToD Optimization)
BESCOM charges a premium (+$1.00/kWh) during peak hours (06:00-09:00, 18:00-22:00) and offers a rebate (-$1.00/kWh) at night (22:00-06:00). 
* **The BESS Solution:** A BESS automatically charges itself at night using cheap power and powers your machines during the morning/evening peaks, pocketing the Rs. 2.00 spread. *(You can observe these rate shifts dynamically in Chart 3 of the dashboard).*

### 3. Diesel Generator (DG) Optimization
* **Curing Low-Load Inefficiency:** Diesel engines burn excess fuel per unit of electricity when running at partial loads (like the 30% load in Case 2). A BESS lets you run the generator at its optimal "sweet spot" (70-80% capacity) to power the factory and charge the battery simultaneously. Once full, the DG shuts off and the battery handles the low load.
* **Handling Micro-Cuts:** BESS can seamlessly handle 15–30 minute outages without ever spinning up the expensive diesel generator.
* **UPS Functionality:** BESS provides a millisecond-reaction power bridge during outages, preventing voltage sags from resetting sensitive factory machinery before the DG takes over.

---

## 📝 Additional Notes

* **Time of Day (ToD) Pricing:** The simulator actively applies ToD pricing to the energy charges. Usage between 06:00–09:00 and 18:00–22:00 incurs a Rs. 1.00 penalty per unit, while nighttime usage (22:00–06:00) receives a Rs. 1.00 rebate.
* **15-Minute Intervals:** Maximum Demand (MD) is calculated based on 15-minute integration periods, which accurately reflects how standard industrial Tri-Vector meters capture peak demand.
* **Data Privacy:** The HTML dashboard relies entirely on client-side JavaScript (using Chart.js via CDN). No data is uploaded to any remote server when you load the CSV files into your browser; all processing happens locally on your machine.