import numpy as np
import pandas as pd
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt
import os

# Resting curve csv
# Manually trim the start to after circuit opens (After voltage stops rapidly increasing)
# Manually trim the end to before voltage starts rapidly decreasing (Before circuit closes)
file_list = ["resting1.csv", "resting2.csv", "resting3.csv"]


def two_rc(t, OCV, A1, tau1, A2, tau2):
    return OCV - A1 * np.exp(-t / tau1) - A2 * np.exp(-t / tau2)

def smooth_tail(voltage: pd.Series):
    rows_to_avg = 10
    tail_start = len(voltage) - int(len(voltage) * 1/1)
    
    smoothed = voltage.copy()
    for i in range(tail_start, len(voltage) - rows_to_avg):
        smoothed.iloc[i] = voltage.iloc[i:i+rows_to_avg].mean()
    return smoothed

plot_data = []
equation = []

for file in file_list:
    try:
        df = pd.read_csv(
            f'Calibration Data/Clean Data/Resting curve fitting/{file}')
    except FileNotFoundError:
        print(f"File not found: {file}")
        continue
    # Time Stamp in milliseconds, Voltage in volts
    
    startTime = df["Time Stamp"][0]
    df["Time Passed Seconds"] = (df["Time Stamp"] - startTime) / 1000

    df["Voltage"] = smooth_tail(df["Voltage"])
    
    voltage = df["Voltage"].values
    time = df["Time Passed Seconds"].values

    # Initial guesses
    OCV_guess = voltage[-1]          # last voltage value
    A1_guess = 0.05           # fast amplitude guess (V)
    tau1_guess = 10             # fast time constant (s)
    A2_guess = 0.01           # slow amplitude guess (V)
    tau2_guess = 200            # slow time constant (s)

    p0 = [OCV_guess, A1_guess, tau1_guess, A2_guess, tau2_guess]

    bounds = (
        [voltage[-1] - 1, 0.0, 0, 0.0, 0],          # lower bounds
        [voltage[-1] + 1, 2.0, 1000, 2.0, 10000]   # upper bounds
    )

    params, covariance = curve_fit(
        two_rc, time, voltage, bounds=bounds, maxfev=10000)
    OCV_fit, A1_fit, tau1_fit, A2_fit, tau2_fit = params

    plot_data.append([time, voltage, two_rc(time, *params)])
    latex_eq = (
        r"$V(t) = OCV"
        rf" - {A1_fit*1000:.1f}\,\mathrm{{mV}} \cdot e^{{-t/{tau1_fit:.1f}\mathrm{{s}}}}"
        rf" - {A2_fit*1000:.1f}\,\mathrm{{mV}} \cdot e^{{-t/{tau2_fit:.1f}\mathrm{{s}}}}$"
    )    
    equation.append(latex_eq)

    print(f"\nFitting results for {file}:")
    print(f"OCV  = {OCV_fit:.4f} V")
    print(f"A1   = {A1_fit*1000:.8f} mV,  τ1 = {tau1_fit:.8f} s")
    print(f"A2   = {A2_fit*1000:.8f} mV,  τ2 = {tau2_fit:.8f} s")
    print(f"V(t) = {OCV_fit:.4f} - {A1_fit*1000:.2f} * exp(-t/{tau1_fit:.2f}) - {A2_fit*1000:.2f} * exp(-t/{tau2_fit:.2f})")

    last_stable_current = df['Last Stable Current'][0]
    print(f"Last Stable Current: {last_stable_current:.2f} A")
    
    R1 = A1_fit / last_stable_current
    C1 = tau1_fit / R1
    R2 = A2_fit / last_stable_current
    C2 = tau2_fit / R2
    print(f"R1 = {R1:.8f} Ω, C1 = {C1:.8f} F")
    print(f"R2 = {R2:.8f} Ω, C2 = {C2:.8f} F")
    
    
fig, ax = plt.subplots(1, len(file_list), figsize=(15, 4))

for i, (time, voltage, fitted) in enumerate(plot_data):
    ax[i].plot(time, voltage, label='Measured', alpha=0.5)
    ax[i].plot(time, fitted, label='2RC fit', linewidth=2)
    ax[i].set_xlabel('Time (s)')
    ax[i].set_ylabel('Voltage (V)')
    ax[i].annotate(equation[i], xy=(0.05, 0.05),
                   xycoords='axes fraction', fontsize=8, verticalalignment='top')
    ax[i].legend()
    ax[i].set_title(f'Fitting Results for {file_list[i]}')

plt.show()
