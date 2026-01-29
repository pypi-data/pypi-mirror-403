###################################################
# Classes to Represent Matrices and Matrix Slices #
###################################################

import multiplied as mp
from typing import Any, Iterator

class Slice:
    """

    """
    def __init__(self, matrix: list[Any]):
        if isinstance(matrix[0], list):
            self.bits = len(matrix[0]) >> 1
        elif isinstance(matrix, list) and isinstance(matrix[0], str):
            self.bits = len(matrix) >> 1
        if self.bits not in mp.SUPPORTED_BITWIDTHS:
            raise ValueError(
                f"Unsupported bitwidth {self.bits}. Expected {mp.SUPPORTED_BITWIDTHS}"
            )
        self.slice = matrix if isinstance(matrix[0], list) else [matrix]

    # TODO:: look into overloads for accurate type usage
    #
    #  index: int -> T
    #  index: slice -> list[T]
    def __getitem__(self, index: int) -> list[Any]:
        slice = [self.slice] if len(self.slice[index]) == 1 else self.slice
        return slice[index]

    def __eq__(self, slice: Any, /) -> bool:
        if slice.bits != self.bits:
            return False
        for i in range(self.bits):
            if slice.slice[i] != self.slice[i]:
                return False
        return True

    def _repr_(self):
        return self.__str__()

    def __str__(self):
        return str(mp.pretty(self.slice))

    def __len__(self) -> int:
        return len(self.slice)

    def __iter__(self) -> Iterator:
        return iter(self.slice)

    def __next__(self):
        if self.index >= len(self.slice):
            raise StopIteration
        self.index += 1
        return self.slice[self.index - 1]






class Matrix:
    """

    """
    def __init__(self, source: Any, *, a: int=0, b: int=0) -> None:
        if isinstance(source, int):
            self.bits = source
        if isinstance(source, list):
            self.bits = len(source)

        if (self.bits not in mp.SUPPORTED_BITWIDTHS):
            raise ValueError(
                f"Unsupported bitwidth {self.bits}. Expected {mp.SUPPORTED_BITWIDTHS}"
            )
        if all([isinstance(a, int), isinstance(b, int), (a != 0 or b != 0)]):
            if not isinstance(source, int):
                raise ValueError("Invalid input. Expected integer.")
            self.matrix = build_matrix(a, b, bits=source).matrix

        elif isinstance(source, int):
            self.bits = source
            self.__empty_matrix(source)

        elif all([isinstance(row, (list, Slice)) for row in source]):
            if len(source)*2 != len(source[0]):
                raise ValueError("Matrix must be 2m * m")
            self.bits = len(source)
            self.matrix = source


    def __empty_matrix(self, bits: int) -> None:
        """
        Build a wallace tree for a bitwidth of self.bits.
        """
        row = [0]*bits
        matrix = []
        for i in range(bits):
            matrix.append(["_"]*(bits-i) + row + ["_"]*i)
        self.matrix = matrix

    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        return mp.pretty(self.matrix)

    def __len__(self) -> int:
        return self.bits

    def __eq__(self, matrix: Any, /) -> bool:
        if matrix.bits != self.bits:
            return False
        for i in range(self.bits):
            if matrix.matrix[i] != self.matrix[i]:
                return False
        return True

    def __getitem__(self, index: int | slice) -> Slice:
        slice = self.matrix[index]
        return Slice(slice)

    def __iter__(self):
        return iter(self.matrix)

    def __next__(self):
        if self.index >= self.bits:
            raise StopIteration
        self.index += 1
        return self.matrix[self.index - 1]

    def resolve_rmap(self, *, ignore_zeros: bool=True
    ) -> mp.Map:
        """
        Find empty rows, create simple map to efficiently pack rows.

        options:
            ignore_zeros: If True, ignore rows with only zeros.
        """

        option = '0' if ignore_zeros else '_'
        offset = 0
        rmap   = []
        for i in range(self.bits):
            if all([bit == '_' and bit != option for bit in self.matrix[i]]):
                offset += 1
                val = 0
            else:
                val = ((offset ^ 255) + 1) # 2s complement
            rmap.append(f"{val:02X}"[-2:])
        return mp.Map(rmap)

    def apply_map(self, map_: mp.Map) -> None:
        """
        """
        if not isinstance(map_, mp.Map):
            raise TypeError(f"Expected Map, got {type(map_)}")
        if map_.bits != self.bits:
            raise ValueError(
                f"Map bitwidth {map_.bits} does not match matrix bitwidth {self.bits}"
            )

        # -- row-wise mapping ---------------------------------------
        if rmap := map_.rmap:
            temp_matrix = build_matrix(0, 0, bits=self.bits).matrix
            for i in range(self.bits):
                # convert signed hex to 2s complement
                if ((val := int(rmap[i], 16)) & 128):
                    val = (~val + 1) & 255 # 2s complement
                temp_matrix[i]     = ["_"] * (self.bits*2)
                temp_matrix[i-val] = self.matrix[i]
            self.matrix = temp_matrix
            return

        # -- bit-wise mapping ---------------------------------------
        raise NotImplementedError("Complex mapping not implemented")



# -- helper functions -----------------------------------------------



def build_matrix(operand_a: int, operand_b: int,*, bits: int=8) -> Matrix:
    """
    Build Logical AND matrix using source operands. Default bits=8
    """
    if bits not in mp.SUPPORTED_BITWIDTHS:
        raise ValueError(
            f"Unsupported bitwidth {bits}. Expected {mp.SUPPORTED_BITWIDTHS}"
        )
    if (operand_a > ((2**bits)-1)) or (operand_b > ((2**bits)-1)):
        raise ValueError("Operand bit width exceeds matrix bit width")

    # convert to binary, removing '0b' and padding with zeros
    a = bin(operand_a)[2:].zfill(bits)
    b = bin(operand_b)[2:].zfill(bits)
    i = 0
    matrix = []
    for i in range(bits-1, -1, -1):
        if b[i] == '0':
            matrix.append(["_"]*(i+1) + ['0']*(bits) + ["_"]*(bits-i-1))
        elif b[i] == '1':
            matrix.append(["_"]*(i+1) + list(a) + ["_"]*(bits-i-1))
    return Matrix(matrix)

def empty_rows(matrix: Matrix) -> int:
    if not isinstance(matrix, Matrix):
        raise TypeError(f"Expected Matrix, got {type(matrix)}")

    empty_row = ['_' for i in range(matrix.bits*2)]
    return sum([matrix.matrix[i] == empty_row for i in range(matrix.bits)])
