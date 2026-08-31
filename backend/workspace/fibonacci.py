"""Modul untuk menghitung bilangan dan deret Fibonacci.

Modul ini menyediakan implementasi fungsi Fibonacci menggunakan
pendekatan rekursif dan iteratif, beserta fungsi pembantu untuk
menghasilkan deret bilangan Fibonacci.
"""

from typing import List


def fibonacci_recursive(n: int) -> int:
    """Menghitung bilangan Fibonacci ke-n secara rekursif.

    Deret Fibonacci didefinisikan sebagai:
        F(0) = 0
        F(1) = 1
        F(n) = F(n-1) + F(n-2) untuk n >= 2

    Args:
        n (int): Indeks bilangan Fibonacci (harus berupa integer non-negatif).

    Returns:
        int: Nilai bilangan Fibonacci ke-n.

    Raises:
        TypeError: Jika input bukan merupakan tipe integer.
        ValueError: Jika input bernilai negatif (n < 0).

    Contoh:
        >>> fibonacci_recursive(0)
        0
        >>> fibonacci_recursive(1)
        1
        >>> fibonacci_recursive(6)
        8
    """
    if not isinstance(n, int) or isinstance(n, bool):
        raise TypeError("Nilai n harus berupa bilangan bulat (integer).")
    if n < 0:
        raise ValueError("Nilai n tidak boleh negatif.")
    if n == 0:
        return 0
    if n == 1:
        return 1

    return fibonacci_recursive(n - 1) + fibonacci_recursive(n - 2)


def fibonacci_iterative(n: int) -> int:
    """Menghitung bilangan Fibonacci ke-n secara iteratif.

    Fungsi ini menggunakan pendekatan perulangan (looping) dengan
    kompleksitas waktu O(n) dan kompleksitas ruang O(1), sehingga
    lebih efisien untuk nilai n yang lebih besar dibandingkan metode rekursif dasar.

    Args:
        n (int): Indeks bilangan Fibonacci (harus berupa integer non-negatif).

    Returns:
        int: Nilai bilangan Fibonacci ke-n.

    Raises:
        TypeError: Jika input bukan merupakan tipe integer.
        ValueError: Jika input bernilai negatif (n < 0).

    Contoh:
        >>> fibonacci_iterative(0)
        0
        >>> fibonacci_iterative(1)
        1
        >>> fibonacci_iterative(10)
        55
    """
    if not isinstance(n, int) or isinstance(n, bool):
        raise TypeError("Nilai n harus berupa bilangan bulat (integer).")
    if n < 0:
        raise ValueError("Nilai n tidak boleh negatif.")
    if n == 0:
        return 0
    if n == 1:
        return 1

    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b


def get_fibonacci_sequence_iterative(count: int) -> List[int]:
    """Menghasilkan deret Fibonacci sebanyak `count` elemen pertama secara iteratif.

    Args:
        count (int): Jumlah elemen deret Fibonacci yang ingin dihasilkan (count >= 0).

    Returns:
        List[int]: Daftar berisi deret bilangan Fibonacci sebanyak `count` elemen.

    Raises:
        TypeError: Jika count bukan merupakan tipe integer.
        ValueError: Jika count bernilai negatif.

    Contoh:
        >>> get_fibonacci_sequence_iterative(7)
        [0, 1, 1, 2, 3, 5, 8]
    """
    if not isinstance(count, int) or isinstance(count, bool):
        raise TypeError("Nilai count harus berupa bilangan bulat (integer).")
    if count < 0:
        raise ValueError("Nilai count tidak boleh negatif.")
    if count == 0:
        return []
    if count == 1:
        return [0]

    sequence = [0, 1]
    while len(sequence) < count:
        sequence.append(sequence[-1] + sequence[-2])
    return sequence


def get_fibonacci_sequence_recursive(count: int) -> List[int]:
    """Menghasilkan deret Fibonacci sebanyak `count` elemen pertama secara rekursif.

    Args:
        count (int): Jumlah elemen deret Fibonacci yang ingin dihasilkan (count >= 0).

    Returns:
        List[int]: Daftar berisi deret bilangan Fibonacci sebanyak `count` elemen.

    Raises:
        TypeError: Jika count bukan merupakan tipe integer.
        ValueError: Jika count bernilai negatif.

    Contoh:
        >>> get_fibonacci_sequence_recursive(7)
        [0, 1, 1, 2, 3, 5, 8]
    """
    if not isinstance(count, int) or isinstance(count, bool):
        raise TypeError("Nilai count harus berupa bilangan bulat (integer).")
    if count < 0:
        raise ValueError("Nilai count tidak boleh negatif.")

    return [fibonacci_recursive(i) for i in range(count)]


if __name__ == "__main__":
    import doctest

    print("Menjalankan doctest...")
    results = doctest.testmod()
    print(f"Hasil pengujian doctest: {results}")

    print("\n--- Demonstrasi Fungsi Fibonacci ---")
    n_contoh = 10

    print(f"1. Fibonacci ke-{n_contoh} (Rekursif) : {fibonacci_recursive(n_contoh)}")
    print(f"2. Fibonacci ke-{n_contoh} (Iteratif) : {fibonacci_iterative(n_contoh)}")

    jumlah_elemen = 10
    print(f"\n3. Deret Fibonacci ({jumlah_elemen} elemen, Iteratif):")
    print(f"   {get_fibonacci_sequence_iterative(jumlah_elemen)}")

    print(f"\n4. Deret Fibonacci ({jumlah_elemen} elemen, Rekursif):")
    print(f"   {get_fibonacci_sequence_recursive(jumlah_elemen)}")
