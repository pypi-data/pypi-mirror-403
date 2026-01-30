arr = [1, 2, 3, 4, 5]

print(sum(arr)/len(arr))

print([x for x in arr if x >= 3])

s = "AbCde"
upper = sum(1 for c in s if c.isupper)

logs = ["INFO", "ERROR", "INFO", "WARN"]
cnt = {}
for log in logs:
    cnt[log] = cnt.get(log, 0) + 1