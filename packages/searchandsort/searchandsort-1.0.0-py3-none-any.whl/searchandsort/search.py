import time

def linear_search(arr, target):
    for index, value in enumerate(arr):
        if value == target:
            return index
    return -1


def linear_search_print(arr, target):
    start = time.perf_counter()
    index = linear_search(arr, target)
    end = time.perf_counter()

    if index != -1:
        print(f"Linear Search: Element {target} found at index {index}")
    else:
        print(f"Linear Search: Element {target} not found")

    print(f"Time Taken: {end - start:.6f} seconds\n")


def binary_search(arr, target):
    low = 0
    high = len(arr) - 1

    while low <= high:
        mid = (low + high) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            low = mid + 1
        else:
            high = mid - 1

    return -1


def binary_search_print(arr, target):
    sorted_arr = sorted(arr)

    start = time.perf_counter()
    index = binary_search(sorted_arr, target)
    end = time.perf_counter()

    if index != -1:
        print(f"Binary Search: Element {target} found at index {index} (in sorted array)")
    else:
        print(f"Binary Search: Element {target} not found")

    print(f"Sorted Array Used: {sorted_arr}")
    print(f"Time Taken: {end - start:.6f} seconds\n")

