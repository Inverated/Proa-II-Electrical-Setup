from configurations.constants import BARE, BARF

def parse_simulation_result(analysis, result, struc, SIMULATION_LOGGING=False, SHOW_PANELS=False):
    if analysis is None:
        return
    
    if SIMULATION_LOGGING:
        print(f"{BARF}Simulation Results:{BARE}")
    
    # Node voltages
    for node_name, node in analysis.nodes.items():
        if "measured" in node_name:
            continue
        matched = False
        for dic in result.values():
            if matched:
                break
            if dic.get("keyword", 'None') in node_name:
                matched = True
                if ":" in node_name and node_name[0:node_name.index(":")].isdigit():
                    prefix = int(node_name[0:node_name.index(":")])
                    if prefix + 1 > len(dic["data"]):
                        dic["data"].extend(eval(struc) for _ in range(prefix - len(dic["data"]) + 1))
                        dic["array_count"] = len(dic["data"])

                    dic["data"][prefix]["voltage"][node_name.replace(f"{prefix}:", "")] = float(node.as_ndarray()[0])
                    dic["data"][prefix]["array_index"] = prefix
                else:
                    if len(dic["data"]) == 0:
                        dic["data"].append(eval(struc))
                        dic["array_count"] += 1
                    dic["data"][0]["voltage"][node_name] = float(node.as_ndarray()[0])

        if not matched:
            print(f"Node {node_name}: {float(node.as_ndarray()[0]):.2f} V")

    # Branch currents
    for branch_name, branch in analysis.branches.items():
        if branch_name.startswith("v"):
            branch_name = branch_name[1:]  # Remove 'v' prefix
        
        if "measured" in branch_name:
                continue
        matched = False
        for dic in result.values():
            if matched:
                break
            if dic.get("keyword", 'None') in branch_name:
                matched = True
                
                if ":" in branch_name and branch_name[0:branch_name.index(":")].isdigit():
                    prefix = int(branch_name[0:branch_name.index(":")])
                    # Add to data list at index i of i:name
                    if prefix + 1 > len(dic["data"]):
                        dic["data"].extend(eval(struc) for _ in range(prefix - len(dic["data"]) + 1))
                        dic["array_count"] = len(dic["data"])
                        
                    dic["data"][prefix]["current"][branch_name.replace(f"{prefix}:", "")] = float(branch.as_ndarray()[0])
                    dic["data"][prefix]["array_index"] = prefix
                else:
                    if len(dic["data"]) == 0:
                        dic["data"].append(eval(struc))
                        dic["array_count"] += 1
                        
                    dic["data"][0]["current"][branch_name] = float(branch.as_ndarray()[0])
        if not matched:
            print(f"Branch {branch_name}: {float(branch.as_ndarray()[0]):.2f} A")

    if SIMULATION_LOGGING:
        for key in result.keys():
            if key == "panel_result" and not SHOW_PANELS:
                continue
            if key in ["error", "warning", "info"]:
                continue

            count = result[key]['array_count']
            print(f"\n{result[key]['keyword'].capitalize()} Results (Count: {count}):")
            for index, data in enumerate(result[key]['data']):
                print(f"{result[key]['keyword'].capitalize()} {index}:") if count > 1 else None
                
                print("\t"*min(1, count) + "Voltages:")
                for node, voltage in data['voltage'].items():
                    print("\t"*min(1, count) + f"\t{node}: {voltage:.2f} V")
                print("\t"*min(1, count) + "Currents:")
                for branch, current in data['current'].items():
                    print("\t"*min(1, count) + f"\t{branch}: {current:.2f} A")
            print(BARE)