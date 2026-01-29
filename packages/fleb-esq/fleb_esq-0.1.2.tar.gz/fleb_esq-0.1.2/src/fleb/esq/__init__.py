"""
Clever docstring goes here.
"""
import typing
from . import ESQ
from . import mode

Mode = mode.Mode
ESQStyle: typing.TypeAlias = typing.Callable[[typing.Any], ESQ.ESQBlock]
ESQBlock = ESQ.ESQBlock
join = ESQ.join

ESQ = ESQ.ESQ

if __name__ == "__main__":
    emph = ESQ.bright.cyan.underline
    print(
        ESQ.yellow("⠕") +
        ESQ.bright.red("⪫") +
        ESQ.bright.yellow.ESQ("⁓ESQ⁓") +
        ESQ.bright.red("⪪") +
        ESQ.yellow("⠪ ") +
        ESQ.cyan.italic(
            emph("E") + "scape " +
            emph("S") + "e" + emph("Q") + "uence" +
            " Generator"
        ))

    print(__doc__)
