
def combinations(n, k):
    # n!/((n-k)!k!)
    result = 1
    for v in range(max(k, n-k) + 1, n + 1):
        result *= v
    for v in range(2, min(k, n-k) + 1):
        result /= v
    return result

def permutations(n, k):
    # n!/(n-k)!
    result = 1
    for v in range(n - k + 1, n + 1):
        result *= v
    return result

def factorial(n):
    # n!
    result = 1
    for v in range(2, n + 1):
        result *= v
    return result
