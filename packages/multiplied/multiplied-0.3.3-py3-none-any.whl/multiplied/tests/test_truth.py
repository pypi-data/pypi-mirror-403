import multiplied as mp



def test_scope() -> None:
    truth = mp.truth_scope((1, 20), (1, 30))
    for t in truth:
        print(t)

def test_shallow_generator4() -> None:
    # truth4  = mp.truth_scope((1, 15), (1, 30))
    # for t in truth4:
    #     print(t)
    truth4  = mp.truth_scope((1, 15), (1, 10))
    matrix4 = mp.Matrix(4)
    alg4    = mp.Algorithm(matrix4)
    for m, a, b in mp.shallow_truth_table(truth4, alg4):
        print(a, b)
        mp.mprint(m)


def test_shallow_generator8() -> None:
    # truth8  = mp.truth_scope((2, 64), (1, 2**15))
    # for t in truth8:
    #     print(t)
    truth8  = mp.truth_scope((2, 64), (1, 22))
    matrix8 = mp.Matrix(8)
    alg8    = mp.Algorithm(matrix8)
    for m, a, b in mp.shallow_truth_table(truth8, alg8):
        print(a, b)
        mp.mprint(m)


def main() -> None:
    # test_scope()
    test_shallow_generator4()
    test_shallow_generator8()


if __name__ == "__main__":
    main()
