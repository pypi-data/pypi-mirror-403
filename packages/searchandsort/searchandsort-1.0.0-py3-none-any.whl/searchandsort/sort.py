import time
import heapq

def bubble_sort(arr):
    a = arr.copy()
    n = len(a)
    for i in range(n):
        for j in range(0, n - i - 1):
            if a[j] > a[j + 1]:
                a[j], a[j + 1] = a[j + 1], a[j]
    return a

def bubble_sort_print(arr):
    start = time.perf_counter()
    result = bubble_sort(arr)
    end = time.perf_counter()
    print("Bubble Sort:", result)
    print(f"Time Taken: {end - start:.6f} seconds\n")


def selection_sort(arr):
    a = arr.copy()
    n = len(a)
    for i in range(n):
        min_idx = i
        for j in range(i + 1, n):
            if a[j] < a[min_idx]:
                min_idx = j
        a[i], a[min_idx] = a[min_idx], a[i]
    return a

def selection_sort_print(arr):
    start = time.perf_counter()
    result = selection_sort(arr)
    end = time.perf_counter()
    print("Selection Sort:", result)
    print(f"Time Taken: {end - start:.6f} seconds\n")


def insertion_sort(arr):
    a = arr.copy()
    for i in range(1, len(a)):
        key = a[i]
        j = i - 1
        while j >= 0 and a[j] > key:
            a[j + 1] = a[j]
            j -= 1
        a[j + 1] = key
    return a

def insertion_sort_print(arr):
    start = time.perf_counter()
    result = insertion_sort(arr)
    end = time.perf_counter()
    print("Insertion Sort:", result)
    print(f"Time Taken: {end - start:.6f} seconds\n")


def merge_sort(arr):
    if len(arr) <= 1:
        return arr
    mid = len(arr) // 2
    left = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])
    return merge(left, right)

def merge(left, right):
    result = []
    i = j = 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    result.extend(left[i:])
    result.extend(right[j:])
    return result

def merge_sort_print(arr):
    start = time.perf_counter()
    result = merge_sort(arr)
    end = time.perf_counter()
    print("Merge Sort:", result)
    print(f"Time Taken: {end - start:.6f} seconds\n")


def quick_sort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    mid = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quick_sort(left) + mid + quick_sort(right)

def quick_sort_print(arr):
    start = time.perf_counter()
    result = quick_sort(arr)
    end = time.perf_counter()
    print("Quick Sort:", result)
    print(f"Time Taken: {end - start:.6f} seconds\n")


def heap_sort(arr):
    a = arr.copy()
    heapq.heapify(a)
    return [heapq.heappop(a) for _ in range(len(a))]

def heap_sort_print(arr):
    start = time.perf_counter()
    result = heap_sort(arr)
    end = time.perf_counter()
    print("Heap Sort:", result)
    print(f"Time Taken: {end - start:.6f} seconds\n")


def counting_sort(arr):
    if not arr:
        return arr
    max_val = max(arr)
    count = [0] * (max_val + 1)
    for num in arr:
        count[num] += 1
    result = []
    for i, c in enumerate(count):
        result.extend([i] * c)
    return result

def counting_sort_print(arr):
    start = time.perf_counter()
    result = counting_sort(arr)
    end = time.perf_counter()
    print("Counting Sort:", result)
    print(f"Time Taken: {end - start:.6f} seconds\n")


def radix_sort(arr):
    a = arr.copy()
    if not a:
        return a
    max_num = max(a)
    exp = 1
    while max_num // exp > 0:
        a = counting_sort_radix(a, exp)
        exp *= 10
    return a

def radix_sort_print(arr):
    start = time.perf_counter()
    result = radix_sort(arr)
    end = time.perf_counter()
    print("Radix Sort:", result)
    print(f"Time Taken: {end - start:.6f} seconds\n")


def counting_sort_radix(arr, exp):
    output = [0] * len(arr)
    count = [0] * 10
    for num in arr:
        index = (num // exp) % 10
        count[index] += 1
    for i in range(1, 10):
        count[i] += count[i - 1]
    for i in range(len(arr) - 1, -1, -1):
        index = (arr[i] // exp) % 10
        output[count[index] - 1] = arr[i]
        count[index] -= 1
    return output


def bucket_sort(arr):
    if not arr:
        return arr
    bucket_count = len(arr)
    buckets = [[] for _ in range(bucket_count)]
    max_val = max(arr)
    for num in arr:
        index = num * bucket_count // (max_val + 1)
        buckets[index].append(num)
    result = []
    for bucket in buckets:
        result.extend(sorted(bucket))
    return result

def bucket_sort_print(arr):
    start = time.perf_counter()
    result = bucket_sort(arr)
    end = time.perf_counter()
    print("Bucket Sort:", result)
    print(f"Time Taken: {end - start:.6f} seconds\n")


def shell_sort(arr):
    a = arr.copy()
    n = len(a)
    gap = n // 2
    while gap > 0:
        for i in range(gap, n):
            temp = a[i]
            j = i
            while j >= gap and a[j - gap] > temp:
                a[j] = a[j - gap]
                j -= gap
            a[j] = temp
        gap //= 2
    return a

def shell_sort_print(arr):
    start = time.perf_counter()
    result = shell_sort(arr)
    end = time.perf_counter()
    print("Shell Sort:", result)
    print(f"Time Taken: {end - start:.6f} seconds\n")


def tim_sort(arr):
    return sorted(arr)

def tim_sort_print(arr):
    start = time.perf_counter()
    result = tim_sort(arr)
    end = time.perf_counter()
    print("Tim Sort:", result)
    print(f"Time Taken: {end - start:.6f} seconds\n")



