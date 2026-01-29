import multiplied as mp



def test_gen_and_tff() -> None:
    testgen = mp.chargen()
    for _ in range(32):
        tmp = next(testgen)
        testtff = mp.chartff(tmp)
        for _ in range(8):
            print(next(testtff), end='')
        print(tmp)

def test_allchars() -> None:
    m = mp.Template(mp.Pattern(['a','a','a','b']))
    print(mp.allchars(m.template))

def main():
    test_gen_and_tff()
    test_allchars()

if __name__ == "__main__":
    main()
