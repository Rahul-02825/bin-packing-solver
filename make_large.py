import random

def planted(seed, k, C, lo, hi):
    random.seed(seed)
    w = []

    for i in range(k):
        left = C

        while left > 0:
            x = min(left, random.randint(lo, hi))

            if 0 < left - x < lo:
                x = left

            w.append(x)
            left -= x

    random.shuffle(w)
    return w

cases = [
    (1, 20, 100, 20, 45),
    (2, 40, 1000, 200, 450)
]


f = open("testcases_large.txt", "w")

f.write("# name | expected | n C weights\n")

for seed, k, C, lo, hi in cases:
    w = planted(seed, k, C, lo, hi)

    line = f"planted_{k} | {k} | {len(w)} {C} "
    line += " ".join(map(str, w)) + "\n"
    f.write(line)

f.close()

print("Test cases generated!")
