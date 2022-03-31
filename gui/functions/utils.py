import numpy as np


def is_acceptable_file(s):
    return s.lower().endswith(('.fit', '.fits'))


def moving_mean(a, m):
    half = m // 2
    second_half = m - half

    a = np.pad(a, (half, second_half), mode='edge')
    print(f"Shape of a = {a.shape}")
    alist = a.tolist()
    start = np.array([a[m:]])

    for i in range(1, m):
        x = i
        y = m-i
        start = np.concatenate((start, np.array([alist[y:-x]])), axis=0)

    print(start[:20])
    print(f"Shape of start = {start.shape}")
    r = np.mean(start.T, axis=1).T
    print(r[:20])
    print(f"Shape of r = {r.shape}")
    return r
