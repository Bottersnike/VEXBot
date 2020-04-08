import json
d = json.load(open("data.json"))
matches = []
for i in d:
    matches += d[i]
from collections import defaultdict
avg = defaultdict(lambda:[])

import random
random.shuffle(matches)

train = matches[len(matches) // 4:]
test = matches[:len(matches) // 4]

sku_avg = {}
for i in d:
    a = []
    for j in d[i]:
        a.append(j["redscore"])
        a.append(j["bluescore"])
    sku_avg[i] = sum(a) / len(a)

for i in train:
    r1, r2 = i["red1"], i["red2"]
    b1, b2 = i["blue1"], i["blue2"]
    m2 = (i["redscore"] - i["bluescore"]) / sku_avg[i["sku"]]
    bs = i["bluescore"]
    rs = i["redscore"]

    bb = -m2 / (i["redscore"] or 1)
    rb = m2 / (i["bluescore"] or 1)

    avg[r1].append((rs, rb))
    avg[r2].append((rs, rb))
    avg[b1].append((bs, bb))
    avg[b2].append((bs, bb))

for i in avg:
    avg[i] = (
        sum(j[0] for j in avg[i]) / len(avg[i]),
        sum(j[1] for j in avg[i]) / len(avg[i])
    )

score = []
errors = []
do = 10
for i in test:
    if i["redscore"] >= i["bluescore"]:
        winner = "red"
    elif i["redscore"] == i["bluescore"]:
        winner = None
    else:
        winner = "blue"
    
    if i["red1"] in avg and i["red2"] in avg and i["blue1"] in avg and i["blue2"] in avg:
        rs = avg[i["red1"]][0]
        if i["red2"]:
            rs += avg[i["red2"]][0]
            rs /= 2
        bs = avg[i["blue1"]][0]
        if i["blue2"]:
            bs += avg[i["blue2"]][0]
            bs /= 2
        
        rb = avg[i["blue1"]][1]
        if i["blue2"]:
            rb += avg[i["blue2"]][1]
            rb /= 2
        nrs = rs - rb * rs
        bb = avg[i["red1"]][1]
        if i["red2"]:
            bb += avg[i["red2"]][1]
            bb /= 2
        bs -= bb * bs
        rs = nrs

        if rs > bs:
            score.append(winner == "red")
        elif rs < bs:
            score.append(winner == "blue")
        
        error = (rs - i["redscore"]) ** 2
        error += (bs - i["bluescore"]) ** 2
        errors.append(error)

        if do:
            print(round(rs), round(bs), "\t\t", i["redscore"], i["bluescore"])
            do -= 1
print(sum(score) / len(score) * 100)
print((sum(errors) / len(errors)) ** 0.5)