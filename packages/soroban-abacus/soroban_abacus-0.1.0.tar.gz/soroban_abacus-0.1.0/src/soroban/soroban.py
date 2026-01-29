import drawsvg as draw


class Column:
    def __init__(self, lower: int, upper: bool):
        if lower < 0 or lower > 5 or not isinstance(lower, int):
            raise ValueError("Provide a valid lower numeral")
        if upper < 0 or upper > 1 or not isinstance(upper, int):
            raise ValueError("Provide a valid upper numeral")

        self.lower: int = lower
        self.upper: int = upper
        self.decimal = self.to_decimal()

    @classmethod
    def from_decimal(cls, decimal: int) -> "Column":
        if (decimal < 0 or decimal > 9) or not isinstance(decimal, int):
            raise ValueError("Provide a valid decimal numeral")
        upper = 0
        if decimal >= 5:
            upper = 1
            decimal -= 5
        lower = decimal
        return cls(lower, upper)

    def to_decimal(self) -> int:
        return self.lower + (self.upper * 5)

    def __repr__(self) -> str:
        upper = "●○" if self.upper == 0 else "○●"
        lower = "●" * self.lower + "○" * (4 - self.lower)
        return f"{upper} | {lower}"


class Soroban:
    def __init__(self, ncolumns: int):
        self.n = ncolumns
        self.columns = [Column(0, 0) for _ in range(ncolumns)]

    def set_columns(self, columns: dict[int, Column]) -> None:
        for index, column in columns.items():
            if index < 0 or index >= self.n:
                raise IndexError("Column index out of range")
            self.columns[index] = column

    def to_decimal(self) -> int:
        total = 0
        power = 1
        for i, column in enumerate(self.columns):
            total += column.to_decimal() * power
            power *= 10
        return total

    def from_decimal(self, decimal: int) -> None:
        if decimal < 0:
            raise ValueError("Provide a non-negative decimal numeral")

        for i in range(self.n):
            digit = decimal % 10
            self.columns[i] = Column.from_decimal(digit)
            decimal //= 10

    def __repr__(self) -> str:
        repr_str = ""
        for i, column in enumerate(self.columns):
            repr_str += f"{i}: {column}\n"
        return repr_str

    def to_svg(self, filename: str | None = None):
        bead_radius = 20
        rod_spacing = 60
        rod_height_upper = 80
        rod_height_lower = 200
        beam_height = 20

        margin = 20

        width = (self.n * rod_spacing) + (margin * 2)
        height = rod_height_upper + beam_height + rod_height_lower + (margin * 2)

        d = draw.Drawing(width, height, origin=(0, 0))

        frame_color = "#8B4513"
        rod_bg_color = "white"
        beam_color = "#5D4037"
        bead_color = "#d32f2f"

        # Frame
        d.append(draw.Rectangle(0, 0, width, height, fill=frame_color, rx=10, ry=10))
        d.append(draw.Rectangle(margin, margin, width - (margin * 2), height - (margin * 2), fill=rod_bg_color, rx=5, ry=5))

        # Beads
        beam_y = margin + rod_height_upper
        d.append(draw.Rectangle(margin, beam_y, width - (margin * 2), beam_height, fill=beam_color))

        for i, column in enumerate(self.columns):
            x_center = width - (margin + (rod_spacing / 2) + (i * rod_spacing))
            d.append(draw.Line(x_center, margin, x_center, height - margin, stroke="black", stroke_width=4))

            bead_y_top = margin + bead_radius
            bead_y_bottom = beam_y - bead_radius

            cy = bead_y_bottom if column.upper == 1 else bead_y_top
            d.append(draw.Circle(x_center, cy, bead_radius, fill=bead_color, stroke="black"))

            earth_start_y = beam_y + beam_height

            active_count = column.lower
            for b in range(active_count):
                cy = earth_start_y + bead_radius + (b * bead_radius * 2)
                d.append(draw.Circle(x_center, cy, bead_radius, fill=bead_color, stroke="black"))

            inactive_count = 4 - active_count
            bottom_limit = height - margin
            for b in range(inactive_count):
                cy = bottom_limit - bead_radius - (b * bead_radius * 2)
                d.append(draw.Circle(x_center, cy, bead_radius, fill=bead_color, stroke="black"))

        if filename:
            d.save_svg(filename)

        return d
