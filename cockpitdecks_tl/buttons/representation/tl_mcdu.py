import logging

from cockpitdecks.buttons.representation.hardware import HardwareRepresentation

from .mcdu import MCDU

logger = logging.getLogger(__file__)
logger.setLevel(logging.DEBUG)
# logger.setLevel(15)


class MCDUScreen(HardwareRepresentation):
    """Displays Toliss Airbus MCDU screen on web deck"""

    REPRESENTATION_NAME = "mcdu"

    PARAMETERS = {}

    def __init__(self, button: "Button"):
        HardwareRepresentation.__init__(self, button=button)

        self.mcduconfig = button._config.get("mcdu", {})  # should not be none, empty at most...
        self.mcdu_unit = self.mcduconfig.get("unit", 1)
        self._datarefs = None
        self.mcdu = MCDU()
        self.mcdu.init(simulator=button.sim)

    def describe(self) -> str:
        return "The representation is specific to Toliss Airbus and display the MCDU screen."

    def get_variables(self) -> set:
        return self.mcdu.get_variables()

    def is_updated(self) -> bool:
        return True

    def get_image_for_icon(self):
        """ """
        if not self.is_updated() and self._cached is not None:
            logger.debug(f"button {self.button.name}: returning cached")
            return self._cached
        # logger.debug(f"button {self.button.name}: creating image")

        image, draw = self.double_icon(width=520, height=400)

        inside = round(0.04 * image.height + 0.5)

        font = self.get_font("HoneywellMCDU.ttf", 26)
        fontsm = self.get_font("HoneywellMCDUSmall.ttf", 22)

        dinfont = self.get_font("DIN.ttf", 26)
        dinfontsm = self.get_font("DIN.ttf", 22)

        if not self.mcdu.draw_text(mcdu_unit=self.mcdu_unit, draw=draw, fonts=[fontsm, font, dinfontsm, dinfont]):
            draw.text((int(image.width / 2), inside + 30), text="MCDU WAITING FOR DATA", font=fontsm, anchor="mb", align="center", fill="#FD8008")

        # Paste image on cockpit background and return it.
        bg = self.button.deck.get_icon_background(
            name=self.button_name,
            width=image.width,
            height=image.height,
            texture_in=None,
            color_in="black",
            use_texture=False,
            who="MCDU",
        )
        bg.alpha_composite(image)

        with open("mcdu_lines.png", "wb") as im:
            bg.save(im, format="PNG")
            # logger.debug(f"button {self.button.name}: saved")

        # self._cached = bg
        # logger.warning(f"button {self.button.name}: image not cached for debug ({bg})")
        return bg
