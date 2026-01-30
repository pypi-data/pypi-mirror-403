cdef class Pos:
    cdef public int line
    cdef public int column

    def __init__(self, int line, int column):
        self.line = line
        self.column = column

    def __hash__(self):
        return hash((self.line, self.column))

    def __eq__(self, other):
        if not isinstance(other, Pos):
            return False
        return self.line == other.line and self.column == other.column

    def __repr__(self):
        return f"Pos(line={self.line}, column={self.column})"
