# `clig` - CLI Generator

A single module, pure python, **Command Line Interface Generator**.

OBS: currently under development.

## Installation

```shell
pip install clig
```

# User guide

`clig` is a single module, written in pure python, that wraps around the
_stdlib_ module [`argparse`](https://docs.python.org/3/library/argparse.html) to
generate command line interfaces through simple functions.

If you know how to use
[`argparse`](https://docs.python.org/3/library/argparse.html), you may want to
use `clig`.

## Basic usage

Create or import some function and call `clig.run()` with it:

```python
# example01.py
import clig

def printperson(name, title="Mister"):
    print(f"{title} {name}")

clig.run(printperson)
```

In general, the function arguments that have a "default" value are turned into
optional _flagged_ (`--`) command line arguments, while the "non default" will
be positional arguments.

```
> python example01.py -h

usage: printperson [-h] [--title TITLE] name

positional arguments:
  name

options:
  -h, --help     show this help message and exit
  --title TITLE
```

The script can then be used in the same way as used with
[`argparse`](https://docs.python.org/3/library/argparse.html):

```
> python example01.py John

Mister John
```

```
> python example01.py Maria --title Miss

Miss Maria
```

You can also pass arguments in code (like with the original
[`parse_args()`](https://docs.python.org/3/library/argparse.html#the-parse-args-method)
method)

```python
>>> import clig
>>> def printperson(name, title="Mister"):
...     print(f"{title} {name}")
...
>>> clig.run(printperson, ["Isaac", "--title", "Sir"])
Sir Isaac
```

The `run()` function accepts
[other arguments to customize the interface](https://github.com/diogo-rossi/clig/tree/main/docs/sphinx/source/notebooks/advancedfeatures.md#parameters-for-cligrun-function)

## Helps

Arguments and command Helps are taken from the docstring when possible:

```python
# example02.py
import clig

def greetings(name, greet="Hello"):
    """Description of the command: A greeting prompt!

    Args:
        name: The name to greet
        greet: The greeting used. Defaults to "Hello".
    """
    print(f"Greetings: {greet} {name}!")

clig.run(greetings)
```

```
> python example02.py --help

usage: greetings [-h] [--greet GREET] name

Description of the command: A greeting prompt!

positional arguments:
  name           The name to greet

options:
  -h, --help     show this help message and exit
  --greet GREET  The greeting used. Defaults to "Hello".
```

There is an internal list of docstring templates from which you can choose if
the inferred docstring is not correct. It is also possible to specify your own
custom docstring template.

## Argument inference

Based on [type annotations](https://docs.python.org/3/library/typing.html), some
arguments can be inferred from the function signature to pass data to the
original
[`add_argument()`](https://docs.python.org/3/library/argparse.html#the-add-argument-method)
method:

```python
# example03.py
import clig

def recordperson(name: str, age: int, height: float):
    print(locals())

clig.run(recordperson)
```

The types in the annotation may be used in the
[`add_argument()`](https://docs.python.org/3/library/argparse.html#the-add-argument-method)
method as [`type`](https://docs.python.org/3/library/argparse.html#type) keyword
argument, when possible:

```
> python example03.py John 37 1.73

{'name': 'John', 'age': 37, 'height': 1.73}
```

And the type conversions are performed as usual

```
> python example03.py Mr John Doe

usage: recordperson [-h] name age height
recordperson: error: argument age: invalid int value: 'John'
```

### Booleans

Booleans are transformed into arguments with
[`action`](https://docs.python.org/3/library/argparse.html#action) of kind
`"store_true"` or `"store_false"` (depending on the default value).

```python
# example04.py
import clig

def recordperson(name: str, employee: bool = False):
    print(locals())

clig.run(recordperson)
```

```
> python example04.py -h

usage: recordperson [-h] [--employee] name

positional arguments:
  name

options:
  -h, --help  show this help message and exit
  --employee
```

```
> python example04.py --employee Leo

{'name': 'Leo', 'employee': True}
```

```
> python example04.py Ana

{'name': 'Ana', 'employee': False}
```

#### Required booleans

If no default is given to the boolean, a
[`required=True`](https://docs.python.org/3/library/argparse.html#required)
keyword argument is used in the
[`add_argument()`](https://docs.python.org/3/library/argparse.html#the-add-argument-method)
method and a
[`BooleanOptionalAction`](https://docs.python.org/3/library/argparse.html#argparse.BooleanOptionalAction)
is used as [`action`](https://docs.python.org/3/library/argparse.html#action)
keyword argument, adding support for a boolean complement action in the form
`--no-option`:

```python
# example05.py
import clig

def recordperson(name: str, employee: bool):
    print(locals())

clig.run(recordperson)
```

```
> python example05.py -h

usage: recordperson [-h] --employee | --no-employee name

positional arguments:
  name

options:
  -h, --help            show this help message and exit
  --employee, --no-employee
```

```
> python example05.py Ana

usage: recordperson [-h] --employee | --no-employee name
recordperson: error: the following arguments are required: --employee/--no-employee
```

### Tuples, Lists and Sequences: [`nargs`](https://docs.python.org/3/library/argparse.html#nargs)

The original [`nargs`](https://docs.python.org/3/library/argparse.html#nargs)
keyword argument associates a different number of command-line arguments with a
single action. This is inferrend in types using `tuple`, `list` and `Sequence`.

#### Tuples

If the type is a `tuple` of specified length `N`, the argument automatically
uses `nargs=N`.

```python
# example06.py
import clig

def main(name: tuple[str, str]):
    print(locals())

clig.run(main)
```

```
> python example06.py -h

usage: main [-h] name name

positional arguments:
  name

options:
  -h, --help  show this help message and exit
```

```
> python example06.py rocky yoco

{'name': ('rocky', 'yoco')}
```

```
> python example06.py rocky

usage: main [-h] name name
main: error: the following arguments are required: name
```

The argument can be positional (required, as above) or optional (with a
default).

```python
# example07.py
import clig

def main(name: tuple[str, str, str] = ("john", "mary", "jean")):
    print(locals())

clig.run(main)
```

```
> python example07.py

{'name': ('john', 'mary', 'jean')}
```

```
> python example07.py --name yoco

usage: main [-h] [--name NAME NAME NAME]
main: error: argument --name: expected 3 arguments
```

```
> python example07.py --name yoco rocky sand

{'name': ('yoco', 'rocky', 'sand')}
```

#### List, Sequences and Tuples of any length

If the type is a generic `Sequence`, a `list` or a `tuple` of _any_ length
(i.e., `tuple[<type>, ...]`), it uses
[`nargs="+"`](https://docs.python.org/3/library/argparse.html#nargs) if it is
required (non default value) or
[`nargs="*"`](https://docs.python.org/3/library/argparse.html#nargs) if it is
not required (has a default value).

```python
# example08.py
import clig

def main(names: list[str]):
    print(locals())

clig.run(main)
```

In this example, we have `names` using
[`nargs="+"`](https://docs.python.org/3/library/argparse.html#nargs)

```
> python example08.py -h

usage: main [-h] names [names ...]

positional arguments:
  names

options:
  -h, --help  show this help message and exit
```

```
> python example08.py chester philip

{'names': ['chester', 'philip']}
```

```
> python example08.py

usage: main [-h] names [names ...]
main: error: the following arguments are required: names
```

In the next example, we have `names` as optional argument, using `nargs="*"`

```python
# example09.py
import clig

def main(names: list[str] | None = None):
    print(locals())

clig.run(main)
```

```
> python example09.py -h

usage: main [-h] [--names [NAMES ...]]

options:
  -h, --help           show this help message and exit
  --names [NAMES ...]
```

```
> python example09.py --names katy buba

{'names': ['katy', 'buba']}
```

```
> python example09.py

{'names': None}
```

### Literals and Enums: [`choices`](https://docs.python.org/3/library/argparse.html#choices)

If the type is a `Literal` or a `Enum` the argument automatically uses
[`choices`](https://docs.python.org/3/library/argparse.html#choices).

```python
# example10.py
from typing import Literal
import clig

def main(name: str, move: Literal["rock", "paper", "scissors"]):
    print(locals())

clig.run(main)
```

```
> python example10.py -h

usage: main [-h] name {rock,paper,scissors}

positional arguments:
  name
  {rock,paper,scissors}

options:
  -h, --help            show this help message and exit
```

As is expected in [`argparse`](https://docs.python.org/3/library/argparse.html),
an error message will be displayed if the argument was not one of the acceptable
values:

```
> python example10.py John knife

usage: main [-h] name {rock,paper,scissors}
main: error: argument move: invalid choice: 'knife' (choose from rock, paper, scissors)
```

```
> python example10.py Mary paper

{'name': 'Mary', 'move': 'paper'}
```

#### Passing Enums

In the command line, `Enum` should be passed by name, regardless of if it is a
number Enum or ar string Enum

```python
# example11.py
from enum import Enum, StrEnum
import clig

class Color(Enum):
    red = 1
    blue = 2
    yellow = 3

class Statistic(StrEnum):
    minimun = "minimun"
    mean = "mean"
    maximum = "maximum"

def main(color: Color, statistic: Statistic):
    print(locals())

clig.run(main)
```

```
> python example11.py -h

usage: main [-h] {red,blue,yellow} {minimun,mean,maximum}

positional arguments:
  {red,blue,yellow}
  {minimun,mean,maximum}

options:
  -h, --help            show this help message and exit
```

It is correctly passed to the function

```
> python example11.py red mean

{'color': <Color.red: 1>, 'statistic': <Statistic.mean: 'mean'>}
```

```
> python example11.py green

usage: main [-h] {red,blue,yellow} {minimun,mean,maximum}
main: error: argument color: invalid choice: 'green' (choose from red, blue, yellow)
```

#### Literal with Enum

You can even mix `Enum` and `Literal`, following the
[`Literal` specification](https://typing.python.org/en/latest/spec/literal.html#legal-parameters-for-literal-at-type-check-time)

```python
# example12.py
from typing import Literal
from enum import Enum
import clig

class Color(Enum):
    red = 1
    blue = 2
    yellow = 3

def main(color: Literal[Color.red, "green", "black"]):
    print(locals())

clig.run(main)
```

```
> python example12.py red

{'color': <Color.red: 1>}
```

```
> python example12.py green

{'color': 'green'}
```

### Variadic arguments (`*args` and `**kwargs`): [Partial parsing](https://docs.python.org/3/library/argparse.html#partial-parsing)

When the function has variadic arguments in the form `*args` or `**kwargs`, the
[parse_known_args()](https://docs.python.org/3/library/argparse.html#argparse.ArgumentParser.parse_known_args)
method will be used internally to gather unspecified arguments:

```python
>>> import clig
>>> def variadics(foo: str, *args, **kwargs):
...     print(locals())
...
>>> clig.run(variadics, "bar badger BAR spam --name adam --title mister".split())
{'foo': 'bar', 'args': ('badger', 'BAR', 'spam'), 'kwargs': {'name': 'adam', 'title': 'mister'}}
```

#### `*args`

For
[arbitrary arguments in the form `*args`](https://docs.python.org/3/tutorial/controlflow.html?utm_source=chatgpt.com#arbitrary-argument-lists),
the unspecified arguments will be wrapped up in a tuple of strings, by default.
If there is a type annotation, the conversion is made in the whole tuple:

```python
>>> import clig
>>> def variadicstyped(number: float, *integers: int):
...     print(locals())
...
>>> clig.run(variadicstyped, ["36.7", "1", "2", "3", "4", "5"])
{'number': 36.7, 'integers': (1, 2, 3, 4, 5)}
```

#### `**kwargs`

For
[arbitrary keyword arguments in the form `**kwargs`](https://docs.python.org/3/tutorial/controlflow.html?utm_source=chatgpt.com#keyword-arguments),
the unspecified arguments will be wrapped up in a dictionary of strings by
default. The keys of the dictionary are the names used with the option delimiter
in the command line (usually `-` or `--`). If there are more than one value for
each option, they are gathered in a list:

```python
# example13.py
import clig

def foobar(name: str, **kwargs):
    print(locals())

clig.run(foobar)
```

```
> python example13.py joseph --nickname joe --uncles jack jean adam

{'name': 'joseph', 'kwargs': {'nickname': 'joe', 'uncles': ['jack', 'jean', 'adam']}}
```

If there is a type annotation, the conversion is made in all elements of the
dictionary

```python
# example14.py
import clig

def foobartyped(name: str, **intergers: int):
    print(locals())

clig.run(foobartyped)
```

```
> python example14.py joseph --age 23 --numbers 25 27 30

{'name': 'joseph', 'intergers': {'age': 23, 'numbers': [25, 27, 30]}}
```

```
> python example14.py joseph --age 23 --numbers jack jean adam

ValueError: invalid literal for int() with base 10: 'jack'
```

#### Error when passing _flagged_ arguments to `*args`

The flag delimiters (usually `-` or `--`,
[which can be changed](https://docs.python.org/3/library/argparse.html#prefix-chars))
are always interpreted as prefix for keyword arguments, raising the correct
error when not allowed:

```python
# example15.py
import clig

def bazham(name: str, *uncles: str):
    print(locals())

clig.run(bazham)
```

```
> python example15.py joseph jack john

{'name': 'joseph', 'uncles': ('jack', 'john')}
```

```
> python example15.py joseph --uncles jack john

TypeError: bazham() got an unexpected keyword argument 'uncles'
```

## Argument specification

In some complex cases supported by
[`argparse`](https://docs.python.org/3/library/argparse.html), the arguments may
not be completely inferred by `clig.run()` on the function signature.

In theses cases, you can directly specificy the arguments parameters using the
[`Annotated`](https://docs.python.org/3/library/typing.html#typing.Annotated)
typing (or its `clig`'s alias `Arg`) with its "metadata" created with the
`data()` function.

The `data()` function accepts all possible arguments of the original
[`add_argument()`](https://docs.python.org/3/library/argparse.html#the-add-argument-method)
method:

### name or flags

The
[`name_or_flags`](https://docs.python.org/3/library/argparse.html#name-or-flags)
parameter can be used to define additional flags for the arguments, like `-f` or
`--foo`:

```python
# example16.py
from clig import Arg, data, run

def main(foobar: Arg[str, data("-f", "--foo")] = "baz"):
    print(locals())

run(main)
```

```
> python example16.py -h

usage: main [-h] [-f FOOBAR]

options:
  -h, --help            show this help message and exit
  -f FOOBAR, --foo FOOBAR
```

[`name or flags`](https://docs.python.org/3/library/argparse.html#name-or-flags)
can also be used to turn a positional argument (without default) into a
[`required`](https://docs.python.org/3/library/argparse.html#required) flagged
argument (a _required option_):

```python
# example17.py
from clig import Arg, data, run

def main(foo: Arg[str, data("-f")]):
    print(locals())

run(main)
```

```
> python example17.py -h

usage: main [-h] -f FOO

options:
  -h, --help         show this help message and exit
  -f FOO, --foo FOO
```

```
> python example17.py

usage: main [-h] -f FOO
main: error: the following arguments are required: -f/--foo
```

**Note**:  
As you can see above, `clig` tries to create a _long flag_ (`--`) for the
argument when only _short flags_ (`-`) are defined (but not when long flags are
already defined). However,
[this behavior can be disabled](https://github.com/diogo-rossi/clig/tree/main/docs/sphinx/source/notebooks/advancedfeatures.md).

Some options for the
[`name or flags`](https://docs.python.org/3/library/argparse.html#name-or-flags)
parameter can also be set in the `run()` function

### nargs

Other cases of [`nargs`](https://docs.python.org/3/library/argparse.html#nargs)
can be specified in the `data()` function.

The next example uses an optional argument with
[`nargs="?"`](https://docs.python.org/3/library/argparse.html#nargs) and
[`const`](https://docs.python.org/3/library/argparse.html#const), which brings 3
different behaviors for the optional argument:

- value passed
- value not passed (sets default value)
- option passed without value (sets const value):

```python
>>> from clig import Arg, data, run
...
>>> def main(foo: Arg[str, data(nargs="?", const="c")] = "d"):
...     print(locals())
...
>>> run(main, ["--foo", "YY"])
{'foo': 'YY'}
>>> run(main, [])
{'foo': 'd'}
>>> run(main, ["--foo"])
{'foo': 'c'}
```

The next example makes optional a positional argument (not flagged), by using
[`nargs="?"`](https://docs.python.org/3/library/argparse.html#nargs) and
[`default`](https://docs.python.org/3/library/argparse.html#default) (which
would default to `None`):

```python
>>> from clig import Arg, data, run
>>> def main(foo: Arg[str, data(nargs="?", default="d")]):
...     print(locals())
...
>>> run(main, ["YY"])
{'foo': 'YY'}
>>> run(main, [])
{'foo': 'd'}
```

### action

Other options for the
[`action`](https://docs.python.org/3/library/argparse.html#action) parameter can
also be used in the `data()` function:

```python
>>> from clig import Arg, data, run
>>> def append(foo: Arg[list[str], data(action="append")] = ["0"]):
...     print(locals())
...
>>> def append_const(bar: Arg[list[int], data(action="append_const", const=42)] = [42]):
...     print(locals())
...
>>> def extend(baz: Arg[list[float], data(action="extend")] = [0]):
...     print(locals())
...
>>> def count(ham: Arg[int, data(action="count")] = 0):
...     print(locals())
...
>>> run(append, "--foo 1 --foo 2".split())
{'foo': ['0', '1', '2']}
...
>>> run(append_const, "--bar --bar --bar --bar".split())
{'bar': [42, 42, 42, 42, 42]}
...
>>> run(extend, "--baz 25 --baz 50 65 75".split())
{'baz': [0, 25.0, 50.0, 65.0, 75.0]}
...
>>> run(count, "--ham --ham --ham".split())
{'ham': 3}
```

### metavar

The parameter
[`metavar`](https://docs.python.org/3/library/argparse.html#metavar) is used to
set alternative names in help messages to refer to arguments. By default, they
would be referend as just the argument name, if positional, and the argument
name uppercased, if optional.

```python
# example18.py
from clig import Arg, data, run

def main(ham: Arg[str, data(metavar="YYY")], foo: Arg[str, data("-f", metavar="<foobar>")]):
    print(locals())

run(main)
```

```
> python example18.py -h

usage: main [-h] -f <foobar> YYY

positional arguments:
  YYY

options:
  -h, --help            show this help message and exit
  -f <foobar>, --foo <foobar>
```

Some options for the
[`metavar`](https://docs.python.org/3/library/argparse.html#metavar) argument
[can also be set in the `run()` function](https://github.com/diogo-rossi/clig/tree/main/docs/sphinx/source/notebooks/advancedfeatures.md#parameters-for-cligrun-function).

### help

It is more convenient to specify [helps for arguments in the docstring](#helps).
However, you can define helps using the `data()` function in the same way as in
the original method
[`add_argument()`](https://docs.python.org/3/library/argparse.html#the-add-argument-method).
Helps passed in the `data()` function takes precedence.

```python
# example19.py
from clig import Arg, data, run

def mycommand(number: Arg[int, data(help="a different help for the number")]):
    """Description of the command

    Args:
        number: a number to compute
    """
    pass

run(mycommand)
```

```
> python example19.py -h

usage: mycommand [-h] number

Description of the command

positional arguments:
  number      a different help for the number

options:
  -h, --help  show this help message and exit
```

## Argument groups

The
[`argparse`](https://docs.python.org/3/library/argparse.html#module-argparse)
module has features of
[argument groups](https://docs.python.org/3/library/argparse.html#argument-groups)
and
[mutually exclusive argument groups](https://docs.python.org/3/library/argparse.html#mutual-exclusion).
These features can be used in `clig` with 2 additional classes: `ArgumentGroup`
and `MutuallyExclusiveGroup`.

The object created with these classes can be used in the `group` parameter of
the `data()` function.

Each class accepts all the parameters of the original methods
[`add_argument_group()`](https://docs.python.org/3/library/argparse.html#argparse.ArgumentParser.add_argument_group)
and
[`add_mutually_exclusive_group()`](https://docs.python.org/3/library/argparse.html#argparse.ArgumentParser.add_mutually_exclusive_group).

```python
# example20.py
from clig import Arg, data, run, ArgumentGroup

g = ArgumentGroup(title="Group of arguments", description="This is my group of arguments")

def main(foo: Arg[str, data(group=g)], bar: Arg[int, data(group=g)] = 42):
    print(locals())

run(main)
```

```
> python example20.py -h

usage: main [-h] [--bar BAR] foo

options:
  -h, --help  show this help message and exit

Group of arguments:
  This is my group of arguments

  foo
  --bar BAR
```

Remember that mutually exclusive arguments
[must be optional](https://github.com/python/cpython/blob/7168553c00767689376c8dbf5933a01af87da3a4/Lib/argparse.py#L1805)
(either by using a flag in the `data` function, or by setting a deafult value):

```python
# example21.py
from clig import Arg, data, run, MutuallyExclusiveGroup

g = MutuallyExclusiveGroup()

def main(foo: Arg[str, data("-f", group=g)], bar: Arg[int, data(group=g)] = 42):
    print(locals())

run(main)
```

```
> python example21.py --foo rocky --bar 23

usage: main [-h] [-f FOO | --bar BAR]
main: error: argument --bar: not allowed with argument -f/--foo
```

### Required mutually exclusive group

A `required` argument is accepted by the `MutuallyExclusiveGroup` in the same
way it is done with the original method
[`add_mutually_exclusive_group()`](https://docs.python.org/3/library/argparse.html#argparse.ArgumentParser.add_mutually_exclusive_group)
(to indicate that at least one of the mutually exclusive arguments is required):

```python
# example22.py
from clig import Arg, data, run, MutuallyExclusiveGroup

g = MutuallyExclusiveGroup(required=True)

def main(foo: Arg[str, data(group=g)] = "baz", bar: Arg[int, data(group=g)] = 42):
    print(locals())

run(main)
```

```
> python example22.py -h

usage: main [-h] (--foo FOO | --bar BAR)

options:
  -h, --help  show this help message and exit
  --foo FOO
  --bar BAR
```

```
> python example22.py

usage: main [-h] (--foo FOO | --bar BAR)
main: error: one of the arguments --foo --bar is required
```

### Mutually exclusive group added to an argument group

The `MutuallyExclusiveGroup` constructor class also accepts an additional
`argument_group` parameter, because
[a mutually exclusive group can be added to an argument group](https://github.com/python/cpython/blob/920286d6b296f9971fc79e14ec22966f8f7a7b90/Doc/library/argparse.rst?plain=1#L2028-L2029).

```python
# example23.py
from clig import Arg, data, run, ArgumentGroup, MutuallyExclusiveGroup

ag = ArgumentGroup(title="Group of arguments", description="This is my group")
meg = MutuallyExclusiveGroup(argument_group=ag)

def main(
    foo: Arg[str, data(group=meg)] = "baz",
    bar: Arg[int, data(group=meg)] = 42,
):
    print(locals())

run(main)
```

```
> python example23.py -h

usage: main [-h] [--foo FOO | --bar BAR]

options:
  -h, --help  show this help message and exit

Group of arguments:
  This is my group

  --foo FOO
  --bar BAR
```

However, you can define just the `MutuallyExclusiveGroup` object passing the
parameters of `ArgumentGroup` to the constructor of the former class, which
supports they:

```python
# example24.py
from clig import Arg, data, run, MutuallyExclusiveGroup

g = MutuallyExclusiveGroup(
    title="Group of arguments",
    description="This is my exclusive group of arguments",
)

def main(
    foo: Arg[str, data("-f", group=g)],
    bar: Arg[int, data("-b", group=g)],
):
    print(locals())

run(main)
```

```
> python example24.py -h

usage: main [-h] [-f FOO | -b BAR]

options:
  -h, --help         show this help message and exit

Group of arguments:
  This is my exclusive group of arguments

  -f FOO, --foo FOO
  -b BAR, --bar BAR
```

### The walrus operator (`:=`)

You can do argument group definition all in one single line (in the function
declaration) by using the
[walrus operator](https://docs.python.org/3/reference/expressions.html#assignment-expressions)
(`:=`):

```python
# example25.py
from clig import Arg, data, run, MutuallyExclusiveGroup

def main(
    foo: Arg[str, data(group=(g := MutuallyExclusiveGroup(title="My group")))] = "baz",
    bar: Arg[int, data(group=g)] = 42,
):
    print(locals())

run(main)
```

```
> python example25.py -h

usage: main [-h] [--foo FOO | --bar BAR]

options:
  -h, --help  show this help message and exit

My group:
  --foo FOO
  --bar BAR
```

## Subcommands

Instead of using the function `clig.run()`, you can create an object instance of
the type `Command`, passing your function to its constructor, and call the
`Command.run()` method.

```python
# example26.py
from clig import Command

def main(name:str, age: int, height: float):
    print(locals())

cmd = Command(main)
cmd.run()
```

```
> python example26.py "Carmem Miranda" 42 1.85

{'name': 'Carmem Miranda', 'age': 42, 'height': 1.85}
```

This makes it possible to use some methods to add
[subcommands](https://docs.python.org/3/library/argparse.html#sub-commands). All
subcommands will also be instances of the same class `Command`. There are 4 main
methods available:

- `new_subcommand`: Creates a subcommand and returns the new created `Command`
  instance.
- `add_subcommand`: Creates the subcommand and returns the caller object. This
  is useful to add multiple subcommands in one single line.
- `end_subcommand`: Creates the subcommand and returns the parent of the caller
  object. If the caller doesn't have a parent, an error will be raised. This is
  useful when finishing to add subcommands in the object on a single line.
- `subcommand`: Creates the subcommand and returns the input function unchanged.
  This is a proper method to be used as a
  [function decorator](https://docs.python.org/3/glossary.html#term-decorator).

There are also [2 module functions](#subcommands-using-function-decorators):
`command()` and `subcommand()`. They also returns the functions unchanged, and
so may also be used as decorators.

The functions declared as commands execute sequentially, from a `Command` to its
subcommands.

The `Command()` constructor also accepts other arguments to customize the
interface, and also has other methods, like `print_help()`, analog to the
[original method](https://docs.python.org/3/library/argparse.html#argparse.ArgumentParser.print_help)

### Subcommands using methods

The methods `new_subcommand` and `add_subcommand` can be used to add subcommands
in an usual object oriented code.  
Consider the case below, with 2 levels of subcommands:

```
prog
├─── subfunction1
└─── subfunction2
            └─── subsubfunction
```

You can create the main command object and add subcommands to it after:

```python
>>> from clig import Command
>>> def prog(name: str, age: int):
...     print(locals())
...
>>> def subfunction1(height: float):
...     print(locals())
...
>>> def subfunction2(father: str, mother: str):
...     print(locals())
...
>>> def subsubfunction(city: str, state: str):
...     print(locals())
...
>>> cmd = Command(prog)  # defines the main object
>>> cmd.add_subcommand(subfunction1)  # adds a subcommand to the main object
>>> sub = cmd.new_subcommand(subfunction2)  # adds and returns a new created subcommand object
>>> sub.add_subcommand(subsubfunction)  # adds a subcommand to the subcommand object
...
>>> cmd.print_help()  # main command help
usage: prog [-h] name age {subfunction1,subfunction2} ...

positional arguments:
  name
  age

options:
  -h, --help            show this help message and exit

subcommands:
  {subfunction1,subfunction2}
    subfunction1
    subfunction2
```

Subcommands are correctly handled with their
[subparsers](https://docs.python.org/3/library/argparse.html#argparse.ArgumentParser.add_subparsers).

```python
>>> sub.print_help() # subcommand help
usage: prog name age subfunction2 [-h] father mother {subsubfunction} ...

positional arguments:
  father
  mother

options:
  -h, --help        show this help message and exit

subcommands:
  {subsubfunction}
    subsubfunction
```

Remember that the command functions execute sequentially, from a `Command` to
its subcommands.

```python
>>> # run the main comand with all subcommands
>>> cmd.run("jack 23 subfunction2 michael suzan subsubfunction santos SP".split())
{'name': 'jack', 'age': 23}
{'father': 'michael', 'mother': 'suzan'}
{'city': 'santos', 'state': 'SP'}
...
>>> # run the subcommand with its subcommand
>>> sub.run(["jean", "karen", "subsubfunction", "campos", "RJ"])
{'father': 'jean', 'mother': 'karen'}
{'city': 'campos', 'state': 'RJ'}
```

To access the attributes of a command inside the functions of its subcommands,
check out the feature of the
[`Context`](https://github.com/diogo-rossi/clig/tree/main/docs/sphinx/source/notebooks/advancedfeatures.md#context)
object.

#### All CLI in one statement

Using the 3 methods `new_subcommand`, `add_subcommand` and `end_subcommand` you
can define the whole interface in one single statement (one line of code).

To give a clear example, consider the [Git](https://git-scm.com/) cli interface.
Some of its command's hierarchy is the following:

```
git
├─── status
├─── commit
├─── remote
│    ├─── add
│    ├─── rename
│    └─── remove
└─── submodule
     ├─── init
     └─── update
```

Then, the functions could be declared in the following structure, with the CLI
definition at the end:

```python
# example27.py
from inspect import getframeinfo, currentframe
from pathlib import Path
from clig import Command

def git(exec_path: Path = Path("git"), work_tree: Path = Path("C:/Users")):
    """The git command line interface"""
    print(f"{getframeinfo(currentframe()).function} {locals()}")

def status(branch: str):
    """Show the repository status"""
    print(f"{getframeinfo(currentframe()).function} {locals()}")

def commit(message: str):
    """Record changes to the repository"""
    print(f"{getframeinfo(currentframe()).function} {locals()}")

def remote(verbose: bool = False):
    """Manage remote repositories"""
    print(f"{getframeinfo(currentframe()).function} {locals()}")

def add(name: str, url: str):
    """Add a new remote"""
    print(f"{getframeinfo(currentframe()).function} {locals()}")

def rename(old: str, new: str):
    """Rename an existing remote"""
    print(f"{getframeinfo(currentframe()).function} {locals()}")

def remove(name: str):
    """Remove the remote reference"""
    print(f"{getframeinfo(currentframe()).function} {locals()}")

def submodule(quiet: bool):
    """Manages git submodules"""
    print(f"{getframeinfo(currentframe()).function} {locals()}")

def init(path: Path = Path(".").resolve()):
    """Initialize the submodules recorded in the index"""
    print(f"{getframeinfo(currentframe()).function} {locals()}")

def update(init: bool, path: Path = Path(".").resolve()):
    """Update the registered submodules"""
    print(f"{getframeinfo(currentframe()).function} {locals()}")

######################################################################
# The whole interface is built in the code below
# It could also be placed in a separated file importing the functions

(
    Command(git)
    .add_subcommand(status)
    .add_subcommand(commit)
    .new_subcommand(remote)
        .add_subcommand(add)
        .add_subcommand(rename)
        .end_subcommand(remove)
    .new_subcommand(submodule)
        .add_subcommand(init)
        .end_subcommand(update)
    .run()
)

```

Help for the main command:

```
> python example27.py -h

usage: git [-h] [--exec-path EXEC_PATH] [--work-tree WORK_TREE]
           {status,commit,remote,submodule} ...

The git command line interface

options:
  -h, --help            show this help message and exit
  --exec-path EXEC_PATH
  --work-tree WORK_TREE

subcommands:
  {status,commit,remote,submodule}
    status              Show the repository status
    commit              Record changes to the repository
    remote              Manage remote repositories
    submodule           Manages git submodules
```

Help for the `remote` subcomand:

```
> python example27.py remote -h

usage: git remote [-h] [--verbose] {add,rename,remove} ...

Manage remote repositories

options:
  -h, --help           show this help message and exit
  --verbose

subcommands:
  {add,rename,remove}
    add                Add a new remote
    rename             Rename an existing remote
    remove             Remove the remote reference
```

Help for the `remote rename` subcommand:

```
> python example27.py remote rename -h

usage: git remote rename [-h] old new

Rename an existing remote

positional arguments:
  old
  new

options:
  -h, --help  show this help message and exit
```

Remember: the command functions execute sequentially, from a `Command` to its
subcommands.

```
> python example27.py remote rename oldName newName

git {'exec_path': WindowsPath('git'), 'work_tree': WindowsPath('C:/Users')}
remote {'verbose': False}
rename {'old': 'oldName', 'new': 'newName'}
```

### Subcommands using method decorators

You can define subcommands using the `subcommand()` method as decorator. To do
it, first, create a `Command` instance. The decorator only registries the
functions as commands (it doesn't change their definitions).

```python
# example28.py
from clig import Command

def main(verbose: bool = False):
    """Description for the main command"""
    print(f"{locals()}")

cmd = Command(main) # create the command object

@cmd.subcommand
def foo(a, b):
    """Help for foo sub command"""
    print(f"{locals()}")

@cmd.subcommand
def bar(c, d):
    """Help for bar sub command"""
    print(f"{locals()}")

cmd.run()
```

```
> python example28.py -h

usage: main [-h] [--verbose] {foo,bar} ...

Description for the main command

options:
  -h, --help  show this help message and exit
  --verbose

subcommands:
  {foo,bar}
    foo       Help for foo sub command
    bar       Help for bar sub command
```

**Note:**  
The `cmd` object in the example above could also be created
[without a function](https://github.com/diogo-rossi/clig/tree/main/docs/sphinx/source/notebooks/advancedfeatures.md#calling-cligcommand-without-a-function)
(i.e., `cmd = Command()`)

You could also use de `Command()` constructor as a
[decorator](https://docs.python.org/3/glossary.html#term-decorator). However,
that would redefine the function name as a `Command` instance.

```python
>>> from clig import Command
>>> def main():
...     pass
...
>>> cmd = Command(main) # the `main` function is not affected with this
>>> print(type(main))
<class 'function'>
...
>>> @Command
>>> def main():
...     pass
...
>>> print(type(main)) # now the main function is a `Command` instance
<class 'clig.clig.Command'>
```

Futhermore, by using decorators without arguments, the functions are not
modified but you won't be able to define more than one level of subcommands,
[unless you pass an argument to the decorators](https://github.com/diogo-rossi/clig/tree/main/docs/sphinx/source/notebooks/advancedfeatures.md#method-decorator-with-argument).

### Subcommands using function decorators

As you may notice in the previous example, using decorators without arguments,
(which do not modify functions definitions) does not allow you to declare more
than one level of subcommands.

For these cases, it is more convenient to use the module level functions
`clig.command()` and `clig.subcommand()` as decorators, because they don't
require to define a `Command` object:

```python
# example29.py
from clig import command, subcommand, run

@command
def main(verbose: bool = False):
    """Description for the main command"""
    print(locals())

@subcommand
def foo(a, b):
    """Help for foo sub command"""
    print(locals())

@subcommand
def bar(c, d):
    """Help for bar sub command"""
    print(locals())

run()
```

```
> python example29.py -h

usage: main [-h] [--verbose] {foo,bar} ...

Description for the main command

options:
  -h, --help  show this help message and exit
  --verbose

subcommands:
  {foo,bar}
    foo       Help for foo sub command
    bar       Help for bar sub command
```

However, to define more than one level of subcommands using these function
decorators, you can also
[pass arguments to the functions](https://github.com/diogo-rossi/clig/tree/main/docs/sphinx/source/notebooks/advancedfeatures.md#method-decorator-with-argument),
in a similar way as
[passing an argument to the methods decorators](https://github.com/diogo-rossi/clig/tree/main/docs/sphinx/source/notebooks/advancedfeatures.md#function-decorator-with-argument),
as discussed in the
[Advanced Features](https://github.com/diogo-rossi/clig/tree/main/docs/sphinx/source/notebooks/advancedfeatures.md).
