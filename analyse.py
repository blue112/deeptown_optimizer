import copy

data = open("data.csv").read().split("\n")[:-1]

def computeComponentsPrice(item):
    if len(item["components"]) == 0:
        return item["cost"]
    else:
        total = 0
        for i in item["components"]:
            total += i["quantity"] * computeComponentsPrice(i["item"])

        return total

def getLowLevelComponents(item, quantity=1):
    if len(item["components"]) == 0:
        return [{"name": item["name"], "amount": quantity}]
    else:
        out = []
        for i in item["components"]:
            for c in getLowLevelComponents(i["item"], quantity * i["quantity"]):
                out.append(c)

        return flaten(out)

def flaten(items):
    d = {}
    for i in items:
        if i["name"] in d:
            d[i["name"]]["amount"] += i["amount"]
        else:
            d[i["name"]] = i

    return d.values()

def computeComponentsTime(item):
    if len(item["components"]) == 0:
        return item["unittime"]
    else:
        total = item["unittime"]
        for i in item["components"]:
            total += i["quantity"] * computeComponentsTime(i["item"])

        return total

def getAddedValue(item):
    return -item["valuepersecperunitcomp"]

def parseArea():
    types = ["coal","copper","iron","amber","aluminium","silver","gold","emerald","ruby","topaz","sapphire","amethyst","diamond","alexandrite","titanium","uranium","platinum"]
    data = open("area.csv").read().split("\n")[:-1]

    area = []
    for i in data:
        total = 0
        for x in i.split(";"):
            n = 0
            if len(x) > 0:
                n = float(x)
            total += n

        cur = {"index": len(area) + 1}
        for n in range(len(i.split(";"))):
            num = 0
            val = i.split(";")[n]
            if len(val) > 0:
                num = float(val)
            cur[types[n]] = num / total
        area.append(cur)
    return area

areas = parseArea()

items = {}
for i in data:
    (name, cost, components, time) = i.split(";")
    items[name.lower()] = {
        "name": name.lower(),
        "cost": float(cost),
        "components": components,
        "unittime": float(time)
    }

for i in items:
    itm = items[i]
    outcompo = []
    if len(itm["components"]) > 0:
        components = itm["components"].split(",")

        for c in components:
            if "x" in c:
                (quantity,c) = c.split("x")
                quantity = float(quantity)
            else:
                quantity = 1.0

            componentEntry = items[c.lower()]
            outcompo.append({
                "item": componentEntry,
                "quantity": quantity
            });

    itm["components"] = outcompo

for i in items:
    itm = items[i]
    if len(itm["components"]) == 0:
        itm["totalcost"] = itm["cost"]
        itm["totaltime"] = itm["unittime"]
    else:
        itm["totalcost"] = computeComponentsPrice(itm);
        itm["totaltime"] = computeComponentsTime(itm);

    itm["addedvalue"] = itm["cost"] - itm["totalcost"]
    if itm["totaltime"] > 0:
        itm["valuepersec"] = itm["addedvalue"] / itm["totaltime"]
        num = len(getLowLevelComponents(itm))
        itm["valuepersecperunitcomp"] = itm["valuepersec"] / num
    else:
        itm["valuepersec"] = 0
        itm["valuepersecperunitcomp"] = 0

for i in sorted(items.values(), key=getAddedValue):
    print("%s: %.3f" % (i["name"], i["valuepersecperunitcomp"]))
    #print(flaten(getLowLevelComponents(i)))
    pass

available_miners = [6,6,5,5,5,6,5,5,5,5,5,5,6,5,6,5,6]
mining_rpm = [0,0,0,0,0,8,12,15]
max_level_available = 65
try_to_maximize = 'topaz'

def find_max(areas, try_to_maximize):
    max_found = 0
    area_index = -1
    for i in range(len(areas)):
        if areas[i][try_to_maximize] > max_found:
            max_found = areas[i][try_to_maximize]
            area_index = i

    return area_index

available_miners = sorted(available_miners, key=lambda a: -a)
mining = []
available_areas = copy.deepcopy(areas)

idx = 0
while idx > -1 and len(available_miners) > 0:
    idx = find_max(available_areas, try_to_maximize)
    if idx > -1 and len(available_miners) > 0:
        mining.append({"area": available_areas[idx], "mining_level": available_miners.pop(0)})
        del available_areas[idx]

mining_result = {}
for i in mining:
    rps = mining_rpm[i["mining_level"]] / 60.0
    for n in i["area"]:
        val = i["area"][n]
        if val > 0 and n != "index":
            if n not in mining_result:
                mining_result[n] = 0
            mining_result[n] += val * rps

print("== Max ==")
for i in sorted(mining_result, key=lambda n: -mining_result[n]):
    print("%s: %.2f/s" % (i, mining_result[i]))

for best_item in sorted(items.values(), key=getAddedValue):
    print("\n======== Summary")
    print("Next Best value item: %s (generates %.2f/s)" % (best_item["name"], best_item["valuepersec"]))
    at_once = 2
    persec = best_item["unittime"] / 2
    print("Can craft %d at once, so can craft %.3f per second" % (at_once, 1 / persec))
    print("To do that, I need:")
    ll = getLowLevelComponents(best_item)
    needed = {}
    for i in ll:
        print("%s: %.3f/s" % (i["name"], (i["amount"] * at_once) / persec))
        needed[i["name"]] = (i["amount"] * at_once) / persec
