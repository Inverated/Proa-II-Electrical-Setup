from configurations.constants import EPISON, POWER_MISMATCH_TOLERANCE_PERCENTAGE


def cross_check_result(component_object, result):
    mppt = result["mppt_result"]
    solar = result["solar_result"]
    load = result["load_result"]
    load_balancer = result["load_balancer"]
    
    # Check solar array power into mppt
    set_count = solar["array_count"]
    solar_data = solar["data"]
    mppt_data = mppt["data"]
    for i in range(set_count):
        if component_object.get("mppt") is None:
            continue
        output_curr_limit = component_object["mppt"][i].get_output_limit()
        actual_curr_output = mppt_data[i]["current"]["mppt_output"]
        actual_voltage_output = mppt_data[i]["voltage"]["mppt_output"]

        solar_output_voltage = solar_data[i]["voltage"]["solar_array_output"]
        solar_output_current = solar_data[i]["current"]["solar_array_output"]
        input_power = solar_output_voltage * solar_output_current * component_object["mppt"][i].get_efficiency()
        if output_curr_limit - actual_curr_output < EPISON:
            result["warning"]["data"].append(f"(Array {i}) Excess power input into MPPT due to {output_curr_limit} A output limit. Input Power: {input_power:.2f} W, Output Power: {actual_voltage_output*actual_curr_output:.2f} W")
    
    # Check battery charge
    excess_current = load_balancer['data'][0]["current"]["balancing_load"]
    if excess_current > EPISON:
        result["warning"]["data"].append(f"Battery is overcharged by {excess_current} A")
        
    # Check battery discharge
    for load in load["data"]:
        voltage = float(list(load["voltage"].values())[0])
        current = float(list(load["current"].values())[0])
        actual_power = voltage * current

        mppt_count = len(component_object.get("mppt", []))
        temp_eff_calculation = 0.0
        for i in range(mppt_count):
            temp_eff_calculation += component_object["mppt"][i].get_efficiency()
        average_efficiency = temp_eff_calculation / mppt_count if mppt_count > 0 else 1.0
            
        index = load["array_index"]
        power_rating = component_object["load"][index].power_rating() * average_efficiency
        throttle_setting = component_object["load"][index].throttle_setting()
        actual_throttle = actual_power / power_rating if power_rating > 0 else 0.0

        if (throttle_setting - actual_throttle) * 100 > POWER_MISMATCH_TOLERANCE_PERCENTAGE:
            actual_throttle = actual_power / power_rating if power_rating > 0 else 0.0
            print(actual_throttle, throttle_setting)
            result["warning"]["data"].append(f"Battery array is being over-discharged. Motor {index} has been restricted to {actual_throttle*100:.2f}% instead of {throttle_setting*100:.2f}% throttle level.")
        
        
    
    result["warning"]["array_count"] = len(result["warning"]["data"])
        