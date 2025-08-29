import logging

from cockpitdecks.variable import VariableListener

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


MCDU_ROOT = "AirbusFBW/MCDU"
MCDU_COLORS = {
    "a": "#FD8008",  # BF521A , amber, dark yellow
    "b": "#2FAFDB",
    "g": "#63E224",
    "m": "#DE50DC",
    "s": "#FFFFFF",  # special characters, not a color
    "w": "#DDDDDD",
    "y": "#EEEE00",
    "Lw": "#FFFFFF",  # bold white, bright white
    "Lg": "#00FF00",  # bold white, bright green
}
SLEW_KEYS = "VertSlewKeys"

MCDU_UNIT = "mucdu-unit"


class MCDU(VariableListener):

    def __init__(self) -> None:
        VariableListener.__init__(self, name="MCDU")
        self.variables = None
        self.datarefs = {}
        self.lines = {}
        self._first = True

    def init(self, simulator):
        for varname in self.get_variables():
            var = simulator.get_variable(name=varname)
            var.add_listener(self)
            # self.datarefs[varname] = var
        logger.info(f"MCDU requests {len(self.variables)} variables")

    def get_variables(self) -> set:
        if self.variables is not None:
            return self.variables
        variables = set()
        for mcdu_unit in range(1, 2):
            variables.add(f"{MCDU_ROOT}{mcdu_unit}{SLEW_KEYS}")
            variables = variables | self.get_variables1unit(mcdu_unit=mcdu_unit)
        self.variables = variables
        return variables

    def completed(self) -> bool:
        return len(self.variables) == len(self.datarefs)

    def get_variables1unit(self, mcdu_unit: int = 1) -> set:
        variables = set()
        # label
        for code in ["title", "stitle"]:
            for color in MCDU_COLORS:  # before: "bgwys":
                if code == "stitle" and color == "s":
                    continue  # skip
                variables.add(f"{MCDU_ROOT}{mcdu_unit}{code}{color}")
        # scratchpad
        code = "sp"
        for color in "aw":
            variables.add(f"{MCDU_ROOT}{mcdu_unit}{code}{color}")
        # lines
        for line in range(1, 7):
            for code in ["label", "cont", "scont"]:  # cont = content, scont = content with special characters
                for color in MCDU_COLORS:
                    if code.endswith("cont") and color.startswith("L"):
                        continue  # skip
                    variables.add(f"{MCDU_ROOT}{mcdu_unit}{code}{line}{color}")
        return variables

    def variable_changed(self, variable):
        if not variable.has_changed():
            return
        if not variable.name.startswith(MCDU_ROOT):
            return
        self.datarefs[variable.name] = variable
        mcdu_unit = -1
        try:
            mcdu_unit = int(variable.name[len(MCDU_ROOT)])
        except ValueError:
            logger.warning(f"error for int {variable.name[len(MCDU_ROOT)]}, {variable}")
            return
        # logger.debug(f"MCDU: {variable.name}={variable.value}")
        if not self.completed():  # if got all data
            return
        # At least a value for each variable
        if self._first:
            self._first = False
            logger.info("MCDU read all variables")
            self.build_screen()
        else:  # update changed data
            if SLEW_KEYS in variable.name:
                self.update_sp(mcdu_unit=mcdu_unit)
                return
            if "title" in variable.name:
                self.update_title(mcdu_unit=mcdu_unit)
            elif "sp" in variable.name:
                self.update_sp(mcdu_unit=mcdu_unit)
            else:
                line = variable.name[-2]
                if line == "L":
                    line = variable.name[-3]
                if "label" in variable.name:
                    self.update_label(mcdu_unit=mcdu_unit, line=line)
                else:
                    self.update_line(mcdu_unit=mcdu_unit, line=line)

    def combine(self, l1, l2):
        line = []
        for i in range(24):
            if l1[i][0] == " ":
                line.append(l2[i])
                continue
            if l2[i][0] != " " and l1[i][0] != l2[i][0]:
                logger.debug(f"2 chars {l1[i]} / {l2[i]} ({l1}, {l2})")
            line.append(l1[i])
        return line

    def update_title(self, mcdu_unit: int):
        lines = self.get_line_extra(mcdu_unit=mcdu_unit, what=["title", "stitle"], colors="bgwys")
        self.lines[f"{MCDU_ROOT}{mcdu_unit}title"] = self.combine(lines[0], lines[1])

    def update_sp(self, mcdu_unit: int):
        self.lines[f"{MCDU_ROOT}{mcdu_unit}sp"] = self.get_line_extra(mcdu_unit=mcdu_unit, what=["sp"], colors="aw")[0]

    def update_label(self, mcdu_unit: int, line: int):
        self.lines[f"{MCDU_ROOT}{mcdu_unit}label{line}"] = self.get_line(mcdu_unit=mcdu_unit, line=line, what=["label"], colors=MCDU_COLORS)[0]

    def update_line(self, mcdu_unit: int, line: int):
        lines = self.get_line(mcdu_unit=mcdu_unit, line=line, what=["cont", "scont"], colors=MCDU_COLORS)
        self.lines[f"{MCDU_ROOT}{mcdu_unit}cont{line}"] = self.combine(lines[0], lines[1])

    def get_line_extra(self, mcdu_unit, what, colors):
        lines = []
        for code in what:
            this_line = []
            for c in range(24):
                has_char = []
                for color in colors:
                    if code == "stitle" and color == "s":  # if code in ["stitle", "title"] and color == "s":
                        continue
                    name = f"{MCDU_ROOT}{mcdu_unit}{code}{color}"
                    d = self.datarefs.get(name)
                    if d is None:
                        logger.debug(f"no dataref {name} (mcdu_unit={mcdu_unit}, what={what}, colors={colors}, code={code}, color={color})")
                        continue
                    v = d.value
                    if v is None:
                        # logger.debug(f"no value yet for {name}")
                        continue
                    if c < len(v):
                        if v[c] != " ":
                            has_char.append((v[c], color))
                if len(has_char) == 1:
                    this_line = this_line + has_char
                else:
                    if len(has_char) > 1:
                        logger.debug(f"mutiple char {code}, {c}: {has_char}")
                    this_line.append((" ", "w"))
            # Not fully correct...
            if code == "sp":
                sk = self.datarefs.get(f"{MCDU_ROOT}{mcdu_unit}{SLEW_KEYS}")
                if sk is not None and sk.value == 1:
                    this_line = this_line[:-2]
                    this_line.append(("1", "s"))
                    this_line.append(("4", "s"))
            lines.append(this_line)
        return lines

    def get_line(self, mcdu_unit, line, what, colors):
        lines = []
        for code in what:
            this_line = []
            for c in range(24):
                has_char = []
                for color in colors:
                    if code.endswith("cont") and color.startswith("L"):
                        continue
                    name = f"{MCDU_ROOT}{mcdu_unit}{code}{line}{color}"
                    d = self.datarefs.get(name)
                    if d is None:
                        logger.debug(f"no dataref {name} (mcdu_unit={mcdu_unit}, what={what}, colors={colors}, code={code}, line={line}, color={color})")
                        continue
                    v = d.value
                    if v is None:
                        # logger.debug(f"no value yet for {name}")
                        continue
                    if c < len(v):
                        if v[c] != " ":
                            has_char.append((v[c], color))
                if len(has_char) == 1:
                    this_line = this_line + has_char
                else:
                    if len(has_char) > 1:
                        logger.debug(f"mutiple char {code}, {c}: {has_char}")
                    this_line.append((" ", "w"))
            lines.append(this_line)
        return lines

    def build_screen(self):
        variable = list(self.datarefs.values())[0]
        mcdu_unit = int(variable.name[14])
        self.update_title(mcdu_unit)
        self.update_sp(mcdu_unit)
        for line in range(1, 7):
            self.update_label(mcdu_unit, line)
            self.update_line(mcdu_unit, line)

    def draw_text(self, mcdu_unit: int, draw, fonts, left_offset: int, char_delta: int, interline: int, line_offsets: list, font_sizes: list) -> bool:
        """Returns success"""

        def show_line(src, size, y) -> bool:
            line = self.lines.get(src)
            if line is None:
                logger.debug(f"no line {src}")
                return False
            x = left_offset
            font = fonts[1] if size > 0 else fonts[0]
            for c in line:
                c = (c[0], c[1], font)
                if c[1] == "s":  # "special" characters (rev. eng.)
                    font_alt = fonts[3] if size > 0 else fonts[2]  # special font too...
                    if c[0] == "0":
                        c = ("←", "b", font)
                    elif c[0] == "1":
                        c = ("↑", "w", font)
                    elif c[0] == "2":
                        c = ("←", "w", font)
                    elif c[0] == "3":
                        c = ("→", "w", font)
                    elif c[0] == "4":
                        c = ("↓", "w", font)
                    elif c[0] == "A":
                        c = ("[", "b", font_alt)
                    elif c[0] == "B":
                        c = ("]", "b", font_alt)
                    elif c[0] == "E":
                        c = ("☐", "a", font_alt)  # in searh of larger rectangular box...
                        color = MCDU_COLORS.get(c[1], "white")  # if color is wrong, default to white
                        # draw.rectangle(((x - int(font_sizes[1]/2), y - font_sizes[1] + 2), (x + int(font_sizes[1]/6), y + 1)), outline=color, width=1)
                        bbox = draw.textbbox((x, y), text="I", font=font, anchor="ms")
                        # (left, top, right, bottom), taller, narrower
                        sd = 2
                        bbox = ((bbox[0] + sd, bbox[1] + sd), (bbox[2] - sd, bbox[3] + sd))
                        draw.rectangle(bbox, outline=color, width=1)
                        # print((bbox[2] - bbox[0], bbox[3]-bbox[1]), ( int(font_sizes[1]/2) + int(font_sizes[1]/6), font_sizes[1] + 2 + 1) )
                if c[0] == "`":  # does not print on terminal
                    c = ("°", c[1], font)
                if c[0] != "☐":
                    color = MCDU_COLORS.get(c[1], "white")  # if color is wrong, default to white
                    draw.text((x, y), text=c[0], font=c[2], anchor="ms", fill=color)
                x = x + char_delta
            return True

        if not self.completed():  # if got all data
            # logger.debug("MCDU waiting for data")
            return False

        ret = show_line(f"{MCDU_ROOT}{mcdu_unit}title", size=2, y=line_offsets[0])
        for l in range(1, 7):
            ret = ret and show_line(f"{MCDU_ROOT}{mcdu_unit}label{l}", size=0, y=line_offsets[1] + l * interline)
            ret = ret and show_line(f"{MCDU_ROOT}{mcdu_unit}cont{l}", size=1, y=line_offsets[2] + l * interline)
        ret = ret and show_line(f"{MCDU_ROOT}{mcdu_unit}sp", size=1, y=line_offsets[3])

        return ret
