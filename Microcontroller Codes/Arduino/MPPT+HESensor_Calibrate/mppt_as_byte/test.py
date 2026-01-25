with open("output.txt", "r") as f:
    line = f.readline()
    while line:
        if "Init" in line:
            line = f.readline()
            continue
        row = line.split(" ")
        for each in row:
            if each in ["", "\n"]:
                print()
            else:
                print(chr(int(each)), end="")
            
        line = f.readline()