################################
# Import Modules Without Error #
################################

import multiplied as mp

def test_pop_empty_matrix():
    matrix = mp.Matrix(8)
    assert matrix == matrix
    assert matrix.matrix == [
        ['_', '_', '_', '_', '_', '_', '_', '_', 0, 0, 0, 0, 0, 0, 0, 0],
        ['_', '_', '_', '_', '_', '_', '_', 0, 0, 0, 0, 0, 0, 0, 0, '_'],
        ['_', '_', '_', '_', '_', '_', 0, 0, 0, 0, 0, 0, 0, 0, '_', '_'],
        ['_', '_', '_', '_', '_', 0, 0, 0, 0, 0, 0, 0, 0, '_', '_', '_'],
        ['_', '_', '_', '_', 0, 0, 0, 0, 0, 0, 0, 0, '_', '_', '_', '_'],
        ['_', '_', '_', 0, 0, 0, 0, 0, 0, 0, 0, '_', '_', '_', '_', '_'],
        ['_', '_', 0, 0, 0, 0, 0, 0, 0, 0, '_', '_', '_', '_', '_', '_'],
        ['_', 0, 0, 0, 0, 0, 0, 0, 0, '_', '_', '_', '_', '_', '_', '_']
    ]

def test_pop_build_matrix():
    matrix = mp.build_matrix(0, 0, 8)
    mult_by_zero_a = mp.build_matrix(0, 42, 8)
    mult_by_zero_b = mp.build_matrix(42, 0, 8)
    assert matrix.bits   == mult_by_zero_a.bits
    assert matrix.bits   == mult_by_zero_b.bits
    # print(vars(matrix))
    # print(vars(mult_by_zero_a))
    # print(vars(mult_by_zero_b))

def test_pop_agorithm(): ## POPULATION NO IMPLEMENTED ##
    temp1 = mp.Matrix(8) # Placeholder for template <-- update this
    temp2 = mp.Matrix(8) # Placeholder for template <-- update this
    arg   = [temp1, temp2]
    alg   = mp.Algorithm(temp1)
    alg.populate(arg)

    print(alg.bits)
    print(alg)
    # print(temp1.bits)
    # print(temp2.bits)


def main() -> None:
    test_pop_empty_matrix()
    test_pop_build_matrix()
    test_pop_agorithm()

if __name__ == "__main__":
    main()
