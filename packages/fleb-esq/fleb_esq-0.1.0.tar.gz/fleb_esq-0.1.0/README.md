# ESQ, an Escape SeQuence Generator for Python
https://github.com/SuperFLEB/esq | https://superfleb.github.io/esq | `pip install fleb.esq`

> *"You know what the world needs? Another ANSI escape-code generator for Python!" -- Absolutely Nobody*

In the interest of reinventing wheels, I've written another ANSI color escape code generator to throw onto the pile.
This was originally made to serve as a quick addition to my Blender Addon Template (and other addons), but it makes a
better submodule so I'm passing the savings along to you.

Okay, it does a couple things different. Maybe it's a bit clever. You be the judge.

## Using the thing

Install it with:

```shell
pip install fleb.esq
```

Import it like:
```python
from fleb.esq import ESQ
```

It uses a pretty natural chained format to build styles:
```python
print(ESQ.red.on.blue.underline.blink("This color scheme will be eye-searing, I'm sure."))
```

Chain off of the `ESQ` object, and end with a function call, with the body being a string or another `ESQ`. You can also
nest `ESQ`s and concatenate them to strings or other `ESQ`s with `+`. You don't need to reset your styles-- they revert
themselves and restore the parent style when a block ends.

```python
print(ESQ.red.on.white("Red on white, " + ESQ.green.on.blue("now green on blue, ") + "and back to red on white."))
```

The function returns an `ESQBlock` object that will render the escape codes when printed or cast to a string with `str()`.
The ESQ function itself can be assigned to a variable, creating a reusable shortcut to a style.

```python
from esq import ESQ

# Use str(...) to make it a string.
some_string = str(ESQ.red.on.white.blink("This will result in a string with escape codes in it."))

# It will print in color if you have an ANSI terminal.
print(ESQ.bright.white.on.blue("This will print in color (if you've got an ANSI terminal)"))

# Nesting and concatenation with `+` are supported.
print(ESQ.red("This is red... " + ESQ.on.blue("This is red on blue... " + ESQ.italic("and this is red on blue and italic, which is probably impossible to read."))))

# Save a style for later...
emphasis = ESQ.bright.yellow.italic
print("For when you plan on getting mad " + emphasis("a whole lot") + " and you " + emphasis("really, really") + " mean it!")
```

## Supported colors and styles

"But", I hear you asking, "what _can_ you do with it?"

Well, bucko, you can do... some stuff. I did make this over a week of lunch hours, so it's not _exactly_ packed with
features. Right now, it only supports the basic color set, not any of that fancy 256-color stuff. File an issue to show
you really care, and I might get around to adding things like 256-color support.

But, hey, you didn't pay much and there _are_ a lot of options. Lookit 'em all!

### Colors

* `default` - Use the default color.
* `black`
* `red`
* `green`
* `yellow` - A muddy brown-yellow on some screens, but folks call it yellow
* `brown` - An alias for "yellow" if you're like me and think it's not actually yellow
* `blue`
* `magenta`
* `cyan`
* `white` - The mediocre "enthusiastic gray" white color.
* `light_gray` - An alias for "white", again, if you're like me and think it's not actually white.
* `gray` - An alias for "bright black", because... what even is "bright black"?
* `bright_black`
* `bright_red`
* `bright_green`
* `bright_yellow`
* `bright_blue`
* `bright_magenta`
* `bright_cyan`
* `bright_white`

These can be used as foreground colors-- just say the name-- or as background colors by adding `on.` or `on_`. The
"bright" variation can also be chained with `bright.` or prefixed with `bright_` (see "modifiers" below).

### Modifiers

Subject modifiers (don't type the angle brackets). Subject modifiers can chain with a `.` or be `_` prefixes on
a color or style as appropriate.

* `on.<color>` / `on_<color>` - Set the background color to `<color>`.
* `bright.<color>` / `bright_<color>` - Use the bright variant of the color.
* `no.<style>` / `no_<style>` - Turn off a style (listed below) if it is on.

Style modifiers. Some may or may not work depending on how much extra you paid for your terminal.

* `normal` - Reset styles. (Note `normal` for style, `default` for color.)
* `bold`
* `dim`
* `italic`
* `underline`
* `blink`
* `blink2`
* `reverse`
* `hidden`
* `strike`

```python
ESQ.red.on.white("This is red on white.")

ESQ.on.red("This changes the background to red but leaves the foreground color.")

ESQ.on.white.red("This makes you sound like a pretentious dork or Yoda.")

ESQ.bright.white.underline.italic.strike("Because you just have to hit all the buttons on the elevator to see what happens.")

ESQ.underline("And sometimes you just" + ESQ.no.underline(" need a break from all the underlining ") + "for a bit.")
```

## Utility Functions

(That plural's a lie, there's only one. It's `join`.)

### `join(list[str | ESQBlock], str?)`

Join a list with strings and/or `ESQ` blocks into a single `ESQ` block with an optional glue string.

```python
from esq import ESQ, join

rainbow = [
    ESQ.red('red'),
    "no orange because 16-color ANSI doesn't have it",
    ESQ.yellow('yellow'),
    ESQ.green('green'),
    ESQ.blue('blue'),
    "what's indigo again?"
    "no violet either -- maybe a rainbow was a bad demo idea"
]

print(join(rainbow, " and "))
```

## Mode

By default, ESQ will generate escape codes if STDOUT is a terminal, and will suppress them (print without any codes) if
it is not. It will also jostle the Windows terminal into shape by turning on Virtual Terminal Mode when running in
Windows. (If you don't know what that all means-- it's just a way to make ANSI codes work on some Windows terminals,
such as Git Bash.)

This behavior can be overridden, though, with the `mode` submodule.

```python
from esq import mode
```

What will that get you? A bunch of switches that you usually don't need to twiddle with, but they're there to play with
if you're finicky.

## Mode Values

These Enum values denote the different modes.

- `mode.DISABLED` - ESQ will **not** generate escape codes, regardless of output type.
- `mode.AUTO` - ESQ will detect the output type and generate escape codes if appropriate.
- `mode.ENABLED` - ESQ will **always** generate escape codes, regardless of output type.

## `mode.set(<mode.DISABLED | mode.ENABLED | mode.AUTO>)`

Set the mode. ESQ starts in mode.AUTO and will detect non-TTY STDOUT automatically. You only need to call this if
you want to override that behavior.

```python
from esq import ESQ, mode

mode.set(mode.DISABLED)
print(ESQ.red.on.red("No matter how red I make this, it won't be red."))
```

## `mode.get()`

This returns either `mode.DISABLED` or `mode.ENABLED`, resolving `mode.AUTO` to the actual mode.

```python
from esq import ESQ, mode

# Keep in mind that this only returns mode.ENABLED or mode.DISABLED, so a simple if/else suffices.
if mode.get() == mode.ENABLED:
    print(ESQ.green("Full color!"))
else:
    print("Boring text.")
```

## `mode.init()`

This initializes the terminal to turn on features necessary to properly support ANSI codes. This happens automatically
whenever ESQ generates an escape code. If it is called after a previous `init()` (but before a `revert()`), it will
do nothing.

```python
from esq import ESQ, mode

mode.init()
print(ESQ.red("That was wholly unnecessary, because the first time it hits the \"red\" color code it'll do that anyway."))
```

## `mode.revert()`

This undoes the initialization done by `mode.init()`. This will run automatically when the program exits.

This does **not** change the mode setting, and a subsequent call to ESQ may re-`init()` the terminal if the terminal
type and mode setting should necessitate it.

```python
from esq import ESQ, mode

# If we were on some two-bit Windows terminal that needs a kick in the rear to get its ANSI on, then...
print("\033[31mThis would show escape-code garbage, because I'm adding the codes manually and we haven't run init().\033[0m")
mode.init()
print("\033[31mThis would be red, since I called init().\033[0m")
mode.revert()
print("\033[31mThis would go back to showing escape-code garbage, because I called revert().\033[0m")

print(ESQ.red("This would always show red, because ESQ calls init() automatically"))

# (...and revert() will be called automatically when the program exits so the parent process doesn't get a screwy terminal.)
```
