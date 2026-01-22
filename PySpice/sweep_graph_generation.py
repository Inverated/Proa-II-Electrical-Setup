import matplotlib.pyplot as plt
import numpy as np
from typing import List, Dict, Optional

def generate_graph(results: list, x_axis: list, 
                   voltage_display_choice: list = [], 
                   current_display_choice: list = [], 
                   power_display_choice: list = [], 
                   save_path: str = None):
    """
    Plot current, voltage, and power curves from circuit simulation results.
    
    Parameters:
    -----------
    results : list
        List of result dictionaries from circuit simulations
    x_axis : list
        X-axis values (e.g., throttle_range)
    voltage_display_choice : list
        Categories to plot voltages for (e.g., ['mppt_result', 'solar_result'])
    current_display_choice : list
        Categories to plot currents for
    power_display_choice : list
        Categories to plot power for
    save_path : str, optional
        Path to save the figure. If None, displays instead.
    """
    
    # Count how many subplots we need
    num_plots = sum([len(voltage_display_choice) > 0, 
                     len(current_display_choice) > 0, 
                     len(power_display_choice) > 0])
    
    if num_plots == 0:
        print("No display choices selected")
        return
    
    # Create figure with subplots with more vertical spacing
    fig, axes = plt.subplots(num_plots, 1, figsize=(12, 6 * num_plots))
    if num_plots == 1:
        axes = [axes]
    
    # Adjust spacing between subplots
    plt.subplots_adjust(hspace=0.4, bottom=0.15)
    
    # Collect warnings for annotation
    warning_points = []
    for i, result in enumerate(results):
        if 'warning' in result and result['warning']['array_count'] > 0:
            warning_points.append({
                'x': x_axis[i],
                'warnings': result['warning']['data']
            })
    
    # Color cycles for different traces
    colors = plt.cm.tab10(np.linspace(0, 1, 10))
    
    plot_idx = 0
    
    # Plot Voltage
    if voltage_display_choice:
        ax = axes[plot_idx]
        color_idx = 0
        
        for category in voltage_display_choice:
            voltages = extract_traces(results, category, 'voltage')
            
            for label, values in voltages.items():
                ax.plot(x_axis, values, marker='o', markersize=2, 
                       label=f"{category} - {label}", 
                       color=colors[color_idx % len(colors)])
                color_idx += 1
        
        ax.set_xlabel('Throttle Input')
        ax.set_ylabel('Voltage (V)')
        ax.set_title('Voltage vs Throttle Input')
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        ax.grid(True, alpha=0.3)
        
        # Add warning markers
        if warning_points:
            warning_x = [wp['x'] for wp in warning_points]
            ax.axvline(x=warning_x[0] if warning_x else 0, color='red', 
                      linestyle='--', alpha=0, label='_nolegend_')
            for wp in warning_points:
                ax.axvline(x=wp['x'], color='red', linestyle='--', alpha=0.3)
        
        plot_idx += 1
    
    # Plot Current
    if current_display_choice:
        ax = axes[plot_idx]
        color_idx = 0
        
        for category in current_display_choice:
            currents = extract_traces(results, category, 'current')
            
            for label, values in currents.items():
                ax.plot(x_axis, values, marker='o', markersize=2,
                       label=f"{category} - {label}",
                       color=colors[color_idx % len(colors)])
                color_idx += 1
        
        ax.set_xlabel('Throttle Input')
        ax.set_ylabel('Current (A)')
        ax.set_title('Current vs Throttle Input')
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        ax.grid(True, alpha=0.3)
        
        # Add warning markers
        if warning_points:
            for wp in warning_points:
                ax.axvline(x=wp['x'], color='red', linestyle='--', alpha=0.3)
        
        plot_idx += 1
    
    # Plot Power
    if power_display_choice:
        ax = axes[plot_idx]
        color_idx = 0
        
        for category in power_display_choice:
            power_traces = extract_power_traces(results, category)
            
            for label, values in power_traces.items():
                ax.plot(x_axis, values, marker='o', markersize=2,
                       label=f"{category} - {label}",
                       color=colors[color_idx % len(colors)])
                color_idx += 1
        
        ax.set_xlabel('Throttle Input')
        ax.set_ylabel('Power (W)')
        ax.set_title('Power vs Throttle Input')
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        ax.grid(True, alpha=0.3)
        
        # Add warning markers
        if warning_points:
            for wp in warning_points:
                ax.axvline(x=wp['x'], color='red', linestyle='--', alpha=0.3)
    
    # Add warning text box positioned below all graphs
    if warning_points:
        warning_text = "Warnings:\n"
        for wp in warning_points:
            warning_text += f"x={wp['x']}: {', '.join(wp['warnings'])}\n"
        
        fig.text(0.1, 0.02, warning_text, 
                fontsize=8, color='red', 
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5),
                verticalalignment='bottom')
    
    plt.tight_layout(rect=[0, 0.05, 1, 1])  # Leave space at bottom for warnings
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Graph saved to {save_path}")
    else:
        plt.show()


def extract_traces(results: list, category: str, data_type: str) -> Dict[str, List[float]]:
    """
    Extract voltage or current traces from results.
    
    Returns a dictionary where keys are trace names and values are lists of measurements.
    """
    traces = {}
    
    for result in results:
        if category not in result:
            continue
        
        category_data = result[category]
        
        # Handle different data structures
        if 'data' in category_data:
            for array_item in category_data['data']:
                if data_type not in array_item:
                    continue
                
                for key, value in array_item[data_type].items():
                    # Skip metadata keys
                    if key in ['array_index']:
                        continue
                    
                    # Create trace name
                    trace_name = key
                    if 'array_index' in array_item:
                        trace_name = f"Array{array_item['array_index']}_{key}"
                    
                    # Initialize trace if needed
                    if trace_name not in traces:
                        traces[trace_name] = []
                    
                    # Append value
                    traces[trace_name].append(value)
    
    return traces


def extract_power_traces(results: list, category: str) -> Dict[str, List[float]]:
    """
    Extract power traces (P = V * I) from results.
    """
    power_traces = {}
    
    for result in results:
        if category not in result:
            continue
        
        category_data = result[category]
        
        if 'data' in category_data:
            for array_item in category_data['data']:
                voltages = array_item.get('voltage', {})
                currents = array_item.get('current', {})
                
                # Match voltage and current keys to compute power
                for v_key, v_value in voltages.items():
                    # Try to find matching current key
                    c_key = v_key
                    if c_key in currents:
                        trace_name = v_key
                        if 'array_index' in array_item:
                            trace_name = f"Array{array_item['array_index']}_{v_key}"
                        
                        if trace_name not in power_traces:
                            power_traces[trace_name] = []
                        
                        power = v_value * currents[c_key]
                        power_traces[trace_name].append(power)
    
    return power_traces


# Example usage:
# generate_graph(results, throttle_range, 
#                voltage_display_choice=['mppt_result', 'solar_result', 'load_result', 'battery_result'],
#                current_display_choice=['mppt_result', 'solar_result', 'load_result', 'battery_result'],
#                power_display_choice=['load_result'],
#                save_path=None)