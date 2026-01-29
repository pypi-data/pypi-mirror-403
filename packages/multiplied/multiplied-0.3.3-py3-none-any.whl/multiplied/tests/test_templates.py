###################################################
# Work towards a more elegant solution to testing #
###################################################
import multiplied as mp


def test_temp_build_csa4() -> None:
    matrix4  = mp.Matrix(4)
    slice  = mp.Matrix(4)
    slice  = slice[:3]
    # print(slice)
    my_slice = mp.build_csa('a', slice)
    mp.mprint(matrix4)
    mp.mprint(my_slice[0])
    mp.mprint(my_slice[1])

def test_temp_build_csa8() -> None:
    matrix8  = mp.Matrix(8)
    slice2  = mp.Matrix(8)[3:6]
    my_slice = mp.build_csa('b', slice2)
    mp.mprint(matrix8)
    mp.mprint(my_slice[0])
    mp.mprint(my_slice[1])

def test_temp_build_adder4() -> None:
    matrix4 = mp.Matrix(4)
    slice = mp.Matrix(4)[2:]
    my_slice = mp.build_adder('a', slice)
    mp.mprint(matrix4)
    mp.mprint(my_slice[0])
    mp.mprint(my_slice[1])

def test_temp_build_adder8() -> None:
    matrix4 = mp.Matrix(8)
    slice = mp.Matrix(8)[4:6]
    my_slice = mp.build_adder('a', slice)
    mp.mprint(matrix4)
    mp.mprint(my_slice[0])
    mp.mprint(my_slice[1])

def test_build_from_pattern() -> None:
    mypattern = mp.Pattern([
        'a',
        'a',
        'b',
        'b',
    ])
    mytemplate = mp.Template(mypattern)
    print(mypattern.get_runs())
    print(mytemplate.template)
    print(mytemplate.result)


def test_resolve_rmap() -> None:
    mypattern = mp.Pattern([
        'a',
        'a',
        'b',
        'b',
    ])
    mytemplate = mp.Template(mypattern)
    print(mytemplate)
    # print(mp.Matrix(mytemplate.result))
    print(mp.Matrix(4, a=5, b=4))

def test_resolve_pattern() -> None:
    m = mp.Matrix(8, a=5, b=4)
    mypattern  = mp.resolve_pattern(m)
    mytemplate = mp.Template(mypattern)
    print(mytemplate.__repr__())


def main() -> None:
    # test_temp_build_csa4()
    # test_temp_build_csa8()
    # test_temp_build_adder4()
    # test_temp_build_adder8()
    test_build_from_pattern()
    test_resolve_rmap()
    test_resolve_pattern()


if __name__ == "__main__":
    main()
