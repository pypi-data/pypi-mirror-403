import multiplied as mp
# import pathlib


def test_to_json4():
    truth4  = mp.truth_scope((1, 15), (1, 10))
    matrix4 = mp.Matrix(4)
    alg4    = mp.Algorithm(matrix4)
    filename = 'test_to_json4.json'
    gen = mp.shallow_truth_table(truth4, alg4)
    mp.json_pretty_store(gen, filename)


def test_to_json8():
    truth8  = mp.truth_scope((1, 15), (1, 200))
    matrix8 = mp.Matrix(8)
    alg8    = mp.Algorithm(matrix8)
    filename = 'test_to_json8.json'
    gen = mp.shallow_truth_table(truth8, alg8)
    mp.json_pretty_store(gen, filename)

def main() -> None:
    # test_to_json4()
    test_to_json8()


if __name__ == '__main__':
    main()
