##############################################################################################################
# %%          IMPORTS
##############################################################################################################

from __future__ import annotations

import inspect
import re
import sys
from argparse import ArgumentParser, FileType, HelpFormatter, Action, BooleanOptionalAction, Namespace
from argparse import HelpFormatter, RawTextHelpFormatter, _SubParsersAction  # [_ArgumentParserT]
from argparse import _ArgumentGroup, _MutuallyExclusiveGroup
from dataclasses import KW_ONLY, Field, dataclass, field
from inspect import Parameter
from inspect import _ParameterKind
from types import MappingProxyType, UnionType
from collections import OrderedDict
from collections.abc import Sequence
from typing import get_args, get_origin, Union, Annotated
from typing import Any, Callable, Iterable, Literal, Mapping, Self, TypedDict, Unpack, overload
from enum import Enum, StrEnum

Kind = _ParameterKind
Arg = Annotated

EMPTY = Parameter.empty

##############################################################################################################
# %%          DOCSTRINGS TEMPLATES
##############################################################################################################

DESCRIPTION_DOCSTRING = """{{description}}"""

DESCRIPTION_EPILOG_DOCSTRING = """
    {{description}}    

    {{epilog}}
"""

NUMPY_DOCSTRING_WITH_EPILOG = """
    {{description}}

    {{epilog}}

    Parameters
    ----------
    {{parameter_name}} : {{parameter_type}}
        {{parameter_description}}
"""

NUMPY_DOCSTRING_WITH_EPILOG_NOTYPES = """
    {{description}}

    {{epilog}}

    Parameters
    ----------
    {{parameter_name}}
        {{parameter_description}}
"""

SPHINX_DOCSTRING_WITH_EPILOG = """
{{description}}

{{epilog}}

:param {{parameter_name}}: {{parameter_description}}
:type {{parameter_name}}: {{parameter_type}}
"""

SPHINX_DOCSTRING_WITH_EPILOG_NOTYPES = """
{{description}}

{{epilog}}

:param {{parameter_name}}: {{parameter_description}}
"""

GOOGLE_DOCSTRING_WITH_EPILOG = """
{{description}}

{{epilog}}

Args:
    {{parameter_name}} ({{parameter_type}}): {{parameter_description}}
"""

GOOGLE_DOCSTRING_WITH_EPILOG_NOTYPES = """
{{description}}

{{epilog}}

Args:
    {{parameter_name}}: {{parameter_description}}
"""

GOOGLE_DOCSTRING_NOTYPES = """
{{description}}

Args:
    {{parameter_name}}: {{parameter_description}}
"""

CLIG_DOCSTRING_WITH_EPILOG = """
{{description}}

{{epilog}}

Parameters
----------
- `{{parameter_name}}` {{parameter_type}}
    {{parameter_description}}
"""


NUMPY_DOCSTRING = """
    {{description}}

    Parameters
    ----------
    {{parameter_name}} : {{parameter_type}}
        {{parameter_description}}
"""

SPHINX_DOCSTRING = """
{{description}}

:param {{parameter_name}}: {{parameter_description}}
:type {{parameter_name}}: {{parameter_type}}
"""

GOOGLE_DOCSTRING = """
{{description}}

Args:
    {{parameter_name}} ({{parameter_type}}): {{parameter_description}}
"""

CLIG_DOCSTRING = """
{{description}}

Parameters
----------
- `{{parameter_name}}` {{parameter_type}}
    {{parameter_description}}
"""

CLIG_DOCSTRING_SHORT = """
{{description}}

Parameters
----------
- `{{parameter_name}}` {{parameter_type}}: {{parameter_description}}
"""

# TODO: add 'no type' variants

DOCSTRING_TEMPLATES = [
    NUMPY_DOCSTRING_WITH_EPILOG,
    SPHINX_DOCSTRING_WITH_EPILOG,
    GOOGLE_DOCSTRING_WITH_EPILOG,
    CLIG_DOCSTRING_WITH_EPILOG,
    NUMPY_DOCSTRING_WITH_EPILOG_NOTYPES,
    SPHINX_DOCSTRING_WITH_EPILOG_NOTYPES,
    GOOGLE_DOCSTRING_WITH_EPILOG_NOTYPES,
    GOOGLE_DOCSTRING_NOTYPES,
    NUMPY_DOCSTRING,
    SPHINX_DOCSTRING,
    GOOGLE_DOCSTRING,
    CLIG_DOCSTRING,
    CLIG_DOCSTRING_SHORT,
    DESCRIPTION_DOCSTRING,
    DESCRIPTION_EPILOG_DOCSTRING,
]

SUBPARSERS_DEST = "subcommand_"


class DocStr(StrEnum):
    DESCRIPTION_DOCSTRING = DESCRIPTION_DOCSTRING
    DESCRIPTION_EPILOG_DOCSTRING = DESCRIPTION_EPILOG_DOCSTRING
    NUMPY_DOCSTRING_WITH_EPILOG = NUMPY_DOCSTRING_WITH_EPILOG
    NUMPY_DOCSTRING_WITH_EPILOG_NOTYPES = NUMPY_DOCSTRING_WITH_EPILOG_NOTYPES
    SPHINX_DOCSTRING_WITH_EPILOG = SPHINX_DOCSTRING_WITH_EPILOG
    SPHINX_DOCSTRING_WITH_EPILOG_NOTYPES = SPHINX_DOCSTRING_WITH_EPILOG_NOTYPES
    GOOGLE_DOCSTRING_WITH_EPILOG = GOOGLE_DOCSTRING_WITH_EPILOG
    GOOGLE_DOCSTRING_WITH_EPILOG_NOTYPES = GOOGLE_DOCSTRING_WITH_EPILOG_NOTYPES
    CLIG_DOCSTRING_WITH_EPILOG = CLIG_DOCSTRING_WITH_EPILOG
    NUMPY_DOCSTRING = NUMPY_DOCSTRING
    SPHINX_DOCSTRING = SPHINX_DOCSTRING
    GOOGLE_DOCSTRING = GOOGLE_DOCSTRING
    CLIG_DOCSTRING = CLIG_DOCSTRING
    CLIG_DOCSTRING_SHORT = CLIG_DOCSTRING_SHORT
    GOOGLE_DOCSTRING_NOTYPES = GOOGLE_DOCSTRING_NOTYPES


##############################################################################################################
# %%          MAIN CLASS
##############################################################################################################


@dataclass
class Command:
    func: Callable[..., Any] | None = None
    # Arguments for `ArgumentParser` object, see: https://docs.python.org/3/library/argparse.html#argumentparser-objects
    prog: str | None = None
    usage: str | None = None
    description: str | None = None
    epilog: str | None = None
    parents: Sequence[ArgumentParser] = field(default_factory=list)
    formatter_class: type[HelpFormatter] = RawTextHelpFormatter
    prefix_chars: str = "-"
    fromfile_prefix_chars: str | None = None
    argument_default: Any = None
    conflict_handler: str = "error"
    add_help: bool = True
    allow_abbrev: bool = True
    exit_on_error: bool = True
    # Arguments for `add_subparsers()` method, see: https://docs.python.org/3/library/argparse.html#sub-commands
    _: KW_ONLY
    subcommands_title: str = "subcommands"
    subcommands_description: str | None = None
    subcommands_prog: str | None = None
    subcommands_required: bool = False
    subcommands_help: str | None = None
    subcommands_metavar: str | None = None
    # Arguments for `add_parser()` method, see: https://docs.python.org/3/library/argparse.html#sub-commands
    name: str | None = None
    help: str | None = None
    aliases: Sequence[str] = field(init=False, default_factory=list)
    # Extra arguments of this library
    docstring_template: str | DocStr | None = None
    default_bool: bool = False
    make_flags: bool | None = None
    make_shorts: bool | None = None
    metavarmodifier: str | Sequence[str] | Callable[[str], str] | None = None
    posmetavarmodifier: str | Sequence[str] | Callable[[str], str] | None = None
    optmetavarmodifier: str | Sequence[str] | Callable[[str], str] | None = None
    helpmodifier: Callable[[str], str] | None = None
    poshelpmodifier: Callable[[str], str] | None = None
    opthelpmodifier: Callable[[str], str] | None = None
    help_flags: Sequence[str] = field(default_factory=tuple)
    help_msg: str | None = None
    # Extra arguments of this library not initialized
    parent: Command | None = field(init=False, default=None)
    parser: ArgumentParser | None = field(init=False, default=None)
    # TODO: `make_longs` option
    # TODO: set `func` before init

    def __post_init__(self):

        self.parameters: Mapping[str, Parameter] = {}
        """A dict with `name: Parameter`, where `Parameter` comes from stdlib `inspect`
        ref: https://docs.python.org/3/library/inspect.html#inspect.Parameter"""

        if self.func:
            self.name = self.name or self.func.__name__.replace("_", "-")
            self.parameters = inspect.signature(self.func).parameters

        self.docstring_data: _DocstringData | None = self._get_data_from_docstring()
        self.argument_data: list[_ArgumentData] = self.__generate_argument_data_list()
        if self.docstring_data:
            self.description = self.description or self.docstring_data.description
            self.epilog = self.epilog or self.docstring_data.epilog

        self.sub_commands: OrderedDict[str, Command] = OrderedDict()
        self.sub_commands_group: _SubParsersAction | None = None
        self.longstartflags: str = f"{self.prefix_chars}" * 2

        self._argument_groups: list[ArgumentGroup] = []
        self._mutually_exclusive_groups: list[MutuallyExclusiveGroup] = []

        if self.help_flags or self.help_msg:
            self.add_help = False

        self.opthelpmodifier = self.opthelpmodifier or self.helpmodifier
        self.poshelpmodifier = self.poshelpmodifier or self.helpmodifier
        self.optmetavarmodifier = self.optmetavarmodifier or self.metavarmodifier
        self.posmetavarmodifier = self.posmetavarmodifier or self.metavarmodifier

        self.help_flags = self.help_flags or (("-h", "--help") if self.add_help or self.help_msg else ())

    ##########################################################################################################
    # %:          PUBLIC METHODS
    ##########################################################################################################

    @overload
    def subcommand[**P, T](self, func: Callable[P, T]) -> Callable[P, T]: ...

    @overload
    def subcommand[**P, T](self, **kwargs) -> Callable[[Callable[P, T]], Callable[P, T]]: ...

    def subcommand[**P, T](
        self,
        func: Callable[P, T] | None = None,
        **kwargs,
    ) -> Callable[P, T] | Callable[[Callable[P, T]], Callable[P, T]]:  # fmt: skip
        """Add a subcommand and return the input function unchanged. Suitable to use as decorator."""
        if func is not None:
            self.new_subcommand(func)
            return func

        def wrap(func):
            self.new_subcommand(func, **kwargs)
            return func

        return wrap

    def add_subcommand(self, func: Callable[..., Any], *args, **kwargs) -> Self:
        """Add a subcommand and return the caller object. Suitable to add multiple subcommands in a row."""
        self.new_subcommand(func, *args, **kwargs)
        return self

    def end_subcommand(self, func: Callable[..., Any], *args, **kwargs) -> Command:
        """Add a subcommand and return the parent `Command` instance of the caller object.
        If `parent` attribute is `None`, raise `ValueError`."""
        if self.parent is None:
            raise ValueError(
                "\n\nMethod `end_subcommand()` can not be called by `Command` instances without parent.\n\n"
            )
        self.new_subcommand(func, *args, **kwargs)
        return self.parent

    def new_subcommand(
        self,
        func: Callable[..., Any],
        name: str | None = None,
        help: str | None = None,
        aliases: Sequence[str] | None = None,
        *args,
        **kwargs,
    ) -> Command:
        """Add a subcommand and return the new created subcommand (a new `Command` instance)"""
        # TODO: add `deprecated` included in v3.13
        count = 0
        parent_parser = self.parent
        while parent_parser:
            count += 1
            parent_parser = parent_parser.parent
        cmd: Command = Command(func, *args, **kwargs)
        cmd.name = name or func.__name__
        if not hasattr(self, "subparsers_dest"):
            self.subparsers_dest: str = ""
        self.subparsers_dest = ",".join(
            [self.subparsers_dest[1 : -1 * (count + 1)], cmd.name] if self.subparsers_dest else [cmd.name]
        )
        self.subparsers_dest = "{" + self.subparsers_dest + "}" + " " * count
        cmd.aliases = aliases or []
        cmd.help = help
        cmd.parent = self
        cmd.__sanitize_argument_data_names()
        self.sub_commands.update({cmd.name: cmd})
        return cmd

    def print_help(self):
        if self.parser is None:
            self._add_parsers()
        assert self.parser is not None
        self.parser.print_help()

    def run(self, args: Sequence[str] | None = None) -> Any:
        # TODO: `Context` object
        # TODO: treat variatic argument as parse_know
        # TODO: treat "positional only"?
        if args == None:
            args = sys.argv[1:]
        if self.parser is None:
            self._add_parsers()
        assert self.parser is not None
        namespace: Namespace
        rest: list[str] = []
        starargs: list[str] = []
        starkwargs: dict[str, str] = {}
        if any([argdata.kind in [Kind.VAR_POSITIONAL, Kind.VAR_KEYWORD] for argdata in self.argument_data]):
            namespace, rest = self.parser.parse_known_args(args)
            starargs, starkwargs = self._get_unknown_args(rest)
        else:
            namespace: Namespace = self.parser.parse_args(args)
        # TODO Enum decoverter
        for arg in self.argument_data:
            annotation = arg.typeannotation
            if get_origin(annotation) in [Union, UnionType]:
                annotation = [t for t in get_args(annotation) if t is not type(None)][0]
            if isinstance(annotation, type) and issubclass(annotation, Enum):
                setattr(namespace, arg.name, annotation[getattr(namespace, arg.name)])
            if get_origin(annotation) is Literal:
                types = get_args(annotation)
                for t in types:
                    choice_type = type(t)
                    if issubclass(choice_type, Enum):
                        try:
                            setattr(namespace, arg.name, choice_type[getattr(namespace, arg.name)])
                        except:
                            continue
            if (
                get_origin(annotation) is tuple
                or (isinstance(annotation, type) and issubclass(annotation, tuple))
            ) and (
                arg.kwargs.get("default") is EMPTY
                or arg.kwargs.get("default") != getattr(namespace, arg.name)
            ):
                try:
                    setattr(namespace, arg.name, tuple(getattr(namespace, arg.name)))
                except TypeError:
                    setattr(namespace, arg.name, (getattr(namespace, arg.name)))
        subcommand_name = (
            getattr(namespace, self.subparsers_dest) if hasattr(self, "subparsers_dest") else None
        )
        if self.parent is None:
            self.context = Context(namespace=namespace, command=self)
        else:
            self.context = self.parent.context
        result = None
        if self.func:
            result = self.func(
                *self._get_pos_parameters(namespace, starargs),
                **self._get_kw_parameters(namespace, starkwargs),
            )
        if subcommand_name is not None:
            args = args[args.index(subcommand_name) + 1 :]
            return self.sub_commands[subcommand_name].run(args)
        return result

    ##########################################################################################################
    # %:          PRIVATE METHODS
    ##########################################################################################################

    def __repr__(self, indent: int = 0) -> str:
        return (
            f"{''.ljust(indent)}{'Sub' if self.parent is not None else ''}Command("
            + "".join(
                [
                    f"{"\n".ljust(indent+5)}{name} = {getattr(self,name)}"
                    for name in ["func", "name", "description"]
                ]
            )
            + "".join([f"\n{self.sub_commands[s].__repr__(indent=indent+4)}" for s in self.sub_commands])
            + f"{"\n".ljust(indent+1)})"
        )

    def __generate_argument_data_list(self) -> list[_ArgumentData]:
        argument_data: list[_ArgumentData] = []
        for par in self.parameters:
            data: _ArgumentData = _get_argument_data_from_parameter(self.parameters[par])
            data.help = self.docstring_data.helps.get(data.name, None) if self.docstring_data else None
            argument_data.append(data)
        return argument_data

    def __sanitize_argument_data_names(self) -> None:
        if self.parent:
            names: list[str] = [arg.name for arg in self.parent.argument_data]
            strip_names: list[str] = [n.strip() for n in names]
            for arg in self.argument_data:
                if arg.name.strip() in strip_names:
                    arg.name = names[strip_names.index(arg.name.strip())] + " "

    def _get_pos_parameters(self, namespace: Namespace, starargs: list[str]) -> list[Any]:
        args = []
        for argdata in self.argument_data:
            if argdata.kind not in [
                Kind.POSITIONAL_OR_KEYWORD,
                Kind.POSITIONAL_ONLY,
            ]:
                break
            if _is_context_annotation(argdata.typeannotation):
                args.append(self.context)
            else:
                args.append(_getattr_with_spaces(namespace, argdata.name))
        t = str
        for argdata in self.argument_data:
            if argdata.kind in [Kind.VAR_POSITIONAL]:
                t = argdata.typeannotation if callable(argdata.typeannotation) else str
                break
        args.extend([t(v) for v in starargs])
        return args

    def _get_kw_parameters(self, namespace: Namespace, starkwargs: dict[str, Any]) -> OrderedDict:
        kwargs = OrderedDict(
            {
                argdata.name.strip(): _getattr_with_spaces(namespace, argdata.name)
                for argdata in self.argument_data
                if argdata.kind in [Kind.KEYWORD_ONLY]
                and not (_is_context_annotation(argdata.typeannotation))
            }
        )
        t = str
        for argdata in self.argument_data:
            if isinstance(argdata.typeannotation, type) and issubclass(argdata.typeannotation, Context):
                if argdata.kind in [Kind.KEYWORD_ONLY]:
                    kwargs.update({argdata.name: self.context})
            if argdata.kind in [Kind.VAR_KEYWORD]:
                t = argdata.typeannotation if callable(argdata.typeannotation) else str
                break
        kwargs.update(
            {k: [t(item) for item in v] if isinstance(v, list) else t(v) for k, v in starkwargs.items()}
        )
        return kwargs

    def _get_unknown_args(self, args: list[str]) -> tuple[list[str], dict[str, Any]]:
        pos = []
        i = 0
        while i < len(args) and not args[i].startswith("-"):
            pos.append(args[i])
            i += 1
        opts = {}
        current_key = None
        current_values = []
        while i < len(args):
            token = args[i]
            if token.startswith(self.prefix_chars):
                if current_key is not None:
                    if len(current_values) == 1:
                        opts[current_key] = current_values[0]
                    else:
                        opts[current_key] = current_values
                current_key = token.lstrip(self.prefix_chars)
                current_values = []
            else:
                current_values.append(token)
            i += 1
        if current_key is not None:
            if len(current_values) == 1:
                opts[current_key] = current_values[0]
            else:
                opts[current_key] = current_values
        return pos, opts

    def _get_data_from_docstring(self) -> _DocstringData | None:
        if self.docstring_template:
            return self._collect_docstring_data_using_template(self.docstring_template)
        for template in DOCSTRING_TEMPLATES:
            data: _DocstringData | None = self._collect_docstring_data_using_template(template)
            if data:
                return data
        docstring = _normalize_docstring(self.func.__doc__)
        if docstring:
            return _DocstringData(description=docstring, epilog=None)
        return None

    def _collect_docstring_data_using_template(self, template: str | None = None) -> _DocstringData | None:
        docstring = _normalize_docstring(self.func.__doc__)
        if not docstring:
            return None
        separator: str = "################################" * 30
        template = template or self.docstring_template
        parameter_number = len(
            [
                par
                for par in self.parameters
                if self.parameters[par].kind not in [Kind.VAR_KEYWORD, Kind.VAR_POSITIONAL]
            ]
        )
        # escape for regex match, but not "{" and "}"
        template = re.escape(_normalize_docstring(template) + "\n").replace(r"\{", "{").replace(r"\}", "}")
        place_holders: dict[str, list[int]] = {
            "description": [],
            "epilog": [],
            "parameter_name": [],
            "parameter_type": [],
            "parameter_description": [],
        }
        detected_place_holders: list[str] = re.findall(r"{{.*?}}", template)
        order_counter = 0
        for word in detected_place_holders:
            word = word.removeprefix("{{").removesuffix("}}")
            if word in place_holders:
                place_holders[word].append(order_counter)
                order_counter += 1
        parameter_section_init_index: int = 0
        for i, line in enumerate(template.splitlines()):
            if any([f"{{{{{key}}}}}" in line for key in place_holders if key.startswith("parameter")]):
                parameter_section_init_index = i
                break
        parameter_section_length = sum(
            [template.count(f"{{{{{key}}}}}") for key in place_holders if key.startswith("parameter")]
        )
        if parameter_number > 0 and not parameter_section_length:
            return None
        if parameter_section_length:
            parameter_section = "\n".join(template.splitlines()[parameter_section_init_index:])
            for _ in range(parameter_number - 1):
                template += f"{parameter_section}\n"
        else:
            docstring = docstring.rstrip() + f"\n{separator}"
            template = template.rstrip() + f"\n{re.escape(separator)}\n"
        for place_holder in place_holders:
            template = template.replace(f"{{{{{place_holder}}}}}", "(?! )(.*?)")
        docstring += "\n"
        template += "(?!\\s)(.*?)"
        match = re.match(template, docstring, re.DOTALL)
        if match:
            matches: tuple[str, ...] = match.groups()
            description = matches[place_holders["description"][0]] if place_holders["description"] else None
            epilog = matches[place_holders["epilog"][0]] if place_holders["epilog"] else None
            docstring_data = _DocstringData(description=description, epilog=epilog)
            for i in range(parameter_number):
                docstring_data.helps[
                    matches[place_holders["parameter_name"][0] + parameter_section_length * i]
                ] = _normalize_docstring(
                    matches[place_holders["parameter_description"][0] + parameter_section_length * i].strip()
                )
            return docstring_data
        return None

    def __make_argflagged(self, name: str) -> str:
        return f"{self.longstartflags}{name.replace("_","-")}"

    def __has_long_start_flag(self, flags: Sequence[str]) -> bool:
        return any([flag.startswith(f"{self.longstartflags}") for flag in flags])

    def __has_short_start_flag(self, flags: Sequence[str]) -> bool:
        return any([flag.startswith(self.prefix_chars) and flag[1] != self.prefix_chars for flag in flags])

    def __does_not_have_long_start_flag(self, flags: Sequence[str]) -> bool:
        return not self.__has_long_start_flag(flags)

    def __does_not_have_short_start_flag(self, flags: Sequence[str]) -> bool:
        return not self.__has_short_start_flag(flags)

    def _generate_args_for_add_argument(
        self, argdata: _ArgumentData
    ) -> tuple[tuple[str, ...], _CompleteKeywordArguments]:
        """Helper function to get data from the proxy object and creates (args, kwargs) to `add_argument()`
        Ref: https://docs.python.org/3/library/argparse.html#the-add-argument-method
        """
        # TODO: check variadic args and kwargs
        kwargs: _CompleteKeywordArguments = {
            "dest": argdata.name,
            "help": argdata.kwargs.get("help", argdata.help),
            "default": argdata.kwargs.get("default", argdata.default),
        }
        default_bool = kwargs["default"] if kwargs["default"] is not EMPTY else self.default_bool
        action, nargs, argtype, choices = "store", None, str, None
        kwargs["action"] = argdata.kwargs.get("action") or action
        if argdata.typeannotation is not None:
            action, nargs, argtype, choices = _get_data_from_typeannotation(
                argdata.typeannotation, default_bool, argdata.default, kwargs["action"]
            )
        kwargs["action"] = argdata.kwargs.get("action") or action
        if kwargs["action"] in ["store", "append", "extend"]:
            kwargs["type"] = argdata.kwargs.get("type") or argtype
            kwargs["nargs"] = argdata.kwargs.get("nargs") or nargs
            kwargs["choices"] = argdata.kwargs.get("choices") or choices
        argdata.make_flag = (
            all(
                [
                    argdata.make_flag is None,
                    self.__does_not_have_long_start_flag(argdata.flags),
                    argdata.default is not EMPTY,
                    # kwargs.get("nargs") not in ["*", "?"],
                ]
            )
            or kwargs["action"] in ["store_true", "store_false"]
            or argdata.make_flag
        )
        argflagged: str | None = None
        if (
            argdata.make_flag
            or all(
                [
                    argdata.make_flag is None,
                    argdata.flags,
                    self.__does_not_have_long_start_flag(argdata.flags),
                ]
            )
            or (kwargs["action"] in ["help"] and len(argdata.flags) == 0)
        ):
            argflagged = self.__make_argflagged(argdata.name)
        if argflagged:
            argdata.flags.append(argflagged)
        if kwargs["default"] is EMPTY:
            kwargs["default"] = None
            if argdata.flags:
                if kwargs["action"] in ["help"]:
                    pass
                else:
                    kwargs["required"] = argdata.kwargs.get("required") or True
                    if kwargs["action"] in ["store_true", "store_false"]:
                        kwargs["action"] = BooleanOptionalAction

        # given in `argdata.kwargs` has preference over inferred
        for key in ["metavar", "const", "version"]:
            try:
                kwargs[key] = argdata.kwargs.pop(key)  # type: ignore
            except KeyError:
                pass
        if (
            self.make_shorts
            and self.__has_long_start_flag(argdata.flags)
            and self.__does_not_have_short_start_flag(argdata.flags)
            or (kwargs["action"] in ["help"] and len(argdata.flags) == 0)
        ):
            argdata.flags = [self._make_short_option(argdata.name)] + argdata.flags

        if kwargs["action"] not in ["store_true", "store_false", "help"] and "metavar" not in kwargs:
            if self.optmetavarmodifier is not None and len(argdata.flags) > 0:
                kwargs["metavar"] = self._set_arg_metavar(self.optmetavarmodifier, argdata)
            if self.posmetavarmodifier is not None and len(argdata.flags) == 0:
                kwargs["metavar"] = self._set_arg_metavar(self.posmetavarmodifier, argdata)

        if len(argdata.flags) > 0 and self.opthelpmodifier is not None:
            kwargs["help"] = self.opthelpmodifier(str(kwargs.get("help", "")))
        if len(argdata.flags) == 0 and self.poshelpmodifier is not None:
            kwargs["help"] = self.poshelpmodifier(str(kwargs.get("help", "")))

        return tuple(argdata.flags), kwargs

    def _make_short_option(self, name: str) -> str:
        past_options = list(self.help_flags) + [
            option for argument in self.arguments for option in argument.option_strings
        ]
        for n in range(1, len(name) + 1):
            short_option = f"{self.prefix_chars}{name[:n]}"
            if short_option not in past_options:
                return short_option
            if short_option.upper() not in past_options:
                return short_option.upper()
            short_option = f"{self.prefix_chars}{''.join(p[:n] for p in name.split("_"))}"
            if short_option not in past_options:
                return short_option
        return short_option

    def _set_arg_metavar(
        self, modifier: str | Sequence[str] | Callable[[str], str], argdata: _ArgumentData
    ) -> str | tuple[str, ...] | None:
        if modifier is not None:
            if callable(modifier):
                return modifier(argdata.name)
            if isinstance(modifier, str):
                return modifier
            if isinstance(modifier, Sequence):
                return tuple(modifier)
        return modifier

    def _add_parsers(self) -> None:
        if self.parent is None:
            self.parser = ArgumentParser(
                prog=self.prog or self.name if self.func else None,
                usage=self.usage,
                description=self.description,
                epilog=self.epilog,
                parents=self.parents,
                formatter_class=self.formatter_class,
                prefix_chars=self.prefix_chars,
                fromfile_prefix_chars=self.fromfile_prefix_chars,
                argument_default=self.argument_default,
                conflict_handler=self.conflict_handler,
                add_help=self.add_help,
                allow_abbrev=self.allow_abbrev,
                exit_on_error=self.exit_on_error,
            )
        else:
            if self.parent.parser is None:
                self.parent._add_parsers()
                return
            assert self.parent.sub_commands_group and self.name
            self.parser = self.parent.sub_commands_group.add_parser(
                name=self.name,
                help=self.help or self.description,
                aliases=self.aliases,
                prog=self.prog,
                usage=self.usage,
                description=self.description,
                epilog=self.epilog,
                parents=self.parents,
                formatter_class=self.formatter_class,
                prefix_chars=self.prefix_chars,
                fromfile_prefix_chars=self.fromfile_prefix_chars,
                argument_default=self.argument_default,
                conflict_handler=self.conflict_handler,
                add_help=self.add_help,
                allow_abbrev=self.allow_abbrev,
                exit_on_error=self.exit_on_error,
            )
        self.arguments: list[Action] = []
        assert self.parser is not None
        if (self.help_flags or self.help_msg) and not self.add_help:
            self.help_msg = self.help_msg or "show this help message and exit"
            self.parser.add_argument(*self.help_flags, action="help", help=self.help_msg)
        for argdata in self.argument_data:
            argdata.make_flag = self._set_argumentdata_makeflag(argdata)
            if argdata.kind in [Kind.VAR_KEYWORD, Kind.VAR_POSITIONAL]:
                continue
            if _is_context_annotation(argdata.typeannotation):
                continue
            flags, kwargs = self._generate_args_for_add_argument(argdata)
            handler = self.parser
            if argdata.group is not None:
                group = argdata.group
                if isinstance(group, ArgumentGroup):
                    handler = self._add_argument_group_to_parser(arggroup=group)
                if isinstance(group, MutuallyExclusiveGroup):
                    if "required" in kwargs:
                        kwargs.pop("required")
                    if group.argument_group is not None:
                        handler = self._add_argument_group_to_parser(arggroup=group.argument_group)
                    if group not in self._mutually_exclusive_groups:
                        self._mutually_exclusive_groups.append(group)
                        group._argparse_mutually_exclusive_group = handler.add_mutually_exclusive_group(
                            required=group.required
                        )
                    handler = group._argparse_mutually_exclusive_group

            self.arguments.append(handler.add_argument(*flags, **kwargs))  # type: ignore

        if self.sub_commands and not self.sub_commands_group:
            # ref: https://docs.python.org/3/library/argparse.html#argparse.ArgumentParser.add_subparsers
            self.sub_commands_group = self.parser.add_subparsers(
                title=self.subcommands_title,
                description=self.subcommands_description,
                prog=self.subcommands_prog,  # I corrected this, see https://github.com/python/typeshed/issues/13162
                required=self.subcommands_required,
                help=self.subcommands_help,
                metavar=self.subcommands_metavar,
                dest=self.subparsers_dest,
            )

        for cmd in self.sub_commands:
            self.sub_commands[cmd]._add_parsers()

    def _set_argumentdata_makeflag(self, argdata: _ArgumentData) -> bool | None:
        if argdata.kind in [Kind.VAR_KEYWORD, Kind.KEYWORD_ONLY]:
            return True
        if argdata.make_flag is not None:
            return argdata.make_flag
        if self.make_flags is not None:
            return self.make_flags
        return None

    def _add_argument_group_to_parser(self, arggroup: ArgumentGroup) -> _ArgumentGroup:
        assert self.parser is not None
        if arggroup not in self._argument_groups:
            self._argument_groups.append(arggroup)
            arggroup._argparse_argument_group = self.parser.add_argument_group(
                title=arggroup.title,
                description=arggroup.description,
                argument_default=arggroup.argument_default,
                conflict_handler=arggroup.conflict_handler,
            )
        return arggroup._argparse_argument_group

    @property
    def is_main_command(self) -> bool:
        return self.parent is None


##############################################################################################################
# %%          PRIVATE CLASSES
##############################################################################################################


class _ArgumentMetaDataDictionary(TypedDict, total=False):
    """Dictionary with some parameters passed to the original `add_argument()` method.
    These are expected to be in the argument metadata annotation.
    Namely: `action`, `nargs`, `const`, `choices`, `required`, `help`, `metavar`, `version`.
    The parameter `version` is not documented, but is on some stub.
    The parameters `name_or_flags`, `default`, `type`, `dest` are not passed in this dictionary.
    Ref: https://docs.python.org/3/library/argparse.html#the-add-argument-method
    """

    action: (
        str
        | Literal[
            "store",
            "store_const",
            "store_true",
            "store_false",
            "append",
            "append_const",
            "count",
            "help",
            "version",
            "extend",
        ]
        | type[Action]
    )
    nargs: int | str | None
    const: Any
    choices: Iterable | None
    required: bool | None
    help: str | None
    metavar: str | tuple[str, ...] | None
    version: str | None


class KeywordArguments(_ArgumentMetaDataDictionary, total=False):
    """Dictionary inheriting parameters passed to the original `add_argument()` method,
    including `default` and `type`. These are suppose to be passed to the `add_argument()` method, after
    including `dest` and `name_or_flags`.
    Ref: https://docs.python.org/3/library/argparse.html#the-add-argument-method
    """

    default: Any
    type: type | Callable[[str], Any] | None


class _CompleteKeywordArguments(KeywordArguments, total=False):
    """Dictionary with all parameters passed to the original `add_argument()` method,
    including `dest` . These are suppose to be passed to the `add_argument()` method after
    including `name_or_flags`, which is positional (not a keyword argument).
    Ref: https://docs.python.org/3/library/argparse.html#the-add-argument-method
    """

    dest: str


@dataclass
class _DocstringData:
    """A dataclass with data recovered from docstring"""

    description: str | None
    epilog: str | None
    helps: dict[str, str] = field(default_factory=dict)


@dataclass
class _ArgumentData:
    """A proxy dataclass to store info that came from `inspect.Parameter` objects
    Ref: https://docs.python.org/3/library/inspect.html#inspect.Parameter

    Parameters
    ----------
    - `name` (`str`): Name of the parameter.
    - `typeannotation` (`Callable[[str], Any] | str | FileType | None`, optional): Defaults to `None`.
        Typeannotation of type. When `Annotated`, is the "origin"
    - `kind` (`Kind`, optional): Defaults to `Kind.POSITIONAL_OR_KEYWORD`. See reference.
    - `default` (`Any`, optional): Defaults to `Parameter.empty`. See reference.
    - `flags` (`list[str]`, optional): Defaults to `field(default_factory=list)`. List of flags.
    - `kwargs` (`KeywordArguments`, optional): Defaults to `field(default_factory=KeywordArguments)`.
        Dictionary inheriting parameters passed to the original add_argument() method, including default
        and type. These are suppose to be passed to the add_argument() method, after including dest and
        name_or_flags. Ref: https://docs.python.org/3/library/argparse.html#the-add-argument-method
    - `make_flag` (`bool | None`, optional): Defaults to `None`. Whether to force make flags.
    - `group` (`ArgumentGroup | MutuallyExclusiveGroup | None`, optional): Defaults to `None`.
        Group which the argument belongs
    - `parser` (`Any`, optional): Defaults to `None`. Not used in `clig` (maybe in `dataparsers`?)
    - `help` (`str | None`, optional): Defaults to `None`. Help sting
    """

    name: str
    typeannotation: Callable[[str], Any] | str | FileType | None = None
    kind: Kind = Kind.POSITIONAL_OR_KEYWORD
    default: Any = Parameter.empty
    flags: list[str] = field(default_factory=list)
    kwargs: KeywordArguments = field(default_factory=KeywordArguments)
    make_flag: bool | None = None
    group: ArgumentGroup | MutuallyExclusiveGroup | None = None
    parser: Any = None
    help: str | None = None


##############################################################################################################
# %%          PUBLIC CLASSES
##############################################################################################################


@dataclass
class Context[T]:
    namespace: T
    command: Command


@dataclass
class ArgumentGroup:
    """Ref: https://docs.python.org/3/library/argparse.html#argument-groups"""

    title: str | None = None
    description: str | None = None
    _: KW_ONLY
    argument_default: Any = None
    conflict_handler: str = "error"

    def __post_init__(self):
        self._argparse_argument_group: _ArgumentGroup


@dataclass
class MutuallyExclusiveGroup:
    """Ref: https://docs.python.org/3/library/argparse.html#mutual-exclusion"""

    required: bool = False
    _: KW_ONLY
    argument_group: ArgumentGroup | None = None
    title: str | None = None
    description: str | None = None
    argument_default: Any = None
    conflict_handler: str | None = None

    def __post_init__(self):
        self._argparse_mutually_exclusive_group: _MutuallyExclusiveGroup
        self.__any_argument_group_parameter = any(
            [
                par is not None
                for par in [
                    self.title,
                    self.description,
                    self.argument_default,
                    self.conflict_handler,
                ]
            ]
        )
        if self.argument_group is not None and self.__any_argument_group_parameter:
            raise ValueError("Parameters `argument_group` not allowed with `title`, `description`, etc...")
        if self.__any_argument_group_parameter:
            self.argument_group = ArgumentGroup(
                title=self.title,
                description=self.description,
                argument_default=self.argument_default,
                conflict_handler=self.conflict_handler or "error",
            )


@dataclass
class ArgumentMetaData:
    flags: list[str] = field(default_factory=list)
    make_flag: bool | None = None
    group: ArgumentGroup | MutuallyExclusiveGroup | None = None
    dictionary: KeywordArguments = field(default_factory=KeywordArguments)


##############################################################################################################
# %%          PRIVATE FUNCTIONS
##############################################################################################################


def _is_context_annotation(annotation: Any) -> bool:
    if isinstance(annotation, type):
        return issubclass(annotation, Context)
    annotation = get_origin(annotation)
    if isinstance(annotation, type):
        return issubclass(annotation, Context)
    return False


def _getattr_with_spaces(namespace: Namespace, name: str) -> Any:
    """Like `getattr` but try to get attributes with spaces appended to the names"""
    # Try exact match first
    if hasattr(namespace, name):
        return getattr(namespace, name)

    # Otherwise, keep appending spaces until found
    padded = name
    while True:
        padded += " "
        if hasattr(namespace, padded):
            return getattr(namespace, padded)


def _normalize_docstring(docstring: str | None) -> str:
    """https://peps.python.org/pep-0257/#handling-docstring-indentation

    This functions maybe do the same as `inspect.cleandoc`.
    However, this one accepts `None`.
    """
    if not docstring:
        return ""
    lines: list[str] = docstring.expandtabs(tabsize=4).splitlines()
    indentation: int = min([len(line) - len(line.lstrip()) for line in lines[1:] if line.lstrip()], default=0)
    lines: list[str] = [lines[0].strip()] + [
        line.removeprefix(" " * indentation).rstrip() for line in lines[1:]
    ]
    while lines and not lines[-1]:
        lines.pop()
    while lines and not lines[0]:
        lines.pop(0)
    return "\n".join(lines)


def _get_argument_data_from_parameter(parameter: Parameter) -> _ArgumentData:
    """Helper function to get data from a `inspect.Parameter` object and generetes a proxy object
    Ref: https://docs.python.org/3/library/inspect.html#inspect.Parameter
    """
    argdata: _ArgumentData = _ArgumentData(name=parameter.name, kind=parameter.kind)
    argdata.default = parameter.default
    if parameter.annotation is not EMPTY:
        annotation = parameter.annotation
        if type(annotation) == str:
            annotation = eval(annotation)
        argdata.typeannotation = annotation
        if hasattr(annotation, "__metadata__"):
            argdata.typeannotation = annotation.__origin__
            metadatas = annotation.__metadata__
            for metadata in metadatas:
                if isinstance(metadata, ArgumentMetaData):
                    argdata.flags = metadata.flags.copy()
                    argdata.make_flag = metadata.make_flag
                    argdata.group = metadata.group
                    argdata.kwargs = metadata.dictionary.copy()
                    break
    if parameter.annotation is EMPTY and parameter.default is not EMPTY:
        argdata.typeannotation = type(parameter.default)
    return argdata


def _get_data_from_typeannotation(
    annotation: Any,
    default_bool: bool = False,
    default: Any = None,
    action: str | type[Action] = "store",
) -> tuple[str | type[Action], str | int | None, type | Callable[[str], Any] | None, Sequence[Any] | None]:
    """Return `action`, `nargs`, `argtype`, `choices`"""
    nargs = None
    argtype = annotation if callable(annotation) else str
    choices = None
    origin = get_origin(annotation)
    if origin:
        types = get_args(annotation)
        if origin in [Union, UnionType]:
            types = [t for t in get_args(annotation) if t is not type(None)]
            argtype = __create_union_converter(types)
            inner_origin = get_origin(types[0])
            if inner_origin is tuple:
                inner_types = get_args(types[0])
                nargs = len(inner_types) if Ellipsis not in inner_types else "*"
                nargs = "+" if (nargs == "*" and default is EMPTY) else nargs
            if inner_origin in [list, Sequence]:
                argtype = get_args(types[0])[0]
                nargs = "*"
                nargs = "+" if (nargs == "*" and default is EMPTY) else nargs
        elif origin is tuple:
            nargs = len(types) if Ellipsis not in types else "*"
            argtype = types[0]
            nargs = "+" if (nargs == "*" and default is EMPTY) else nargs
        elif origin in [list, Sequence]:
            nargs = "*" if action != "append" else None
            argtype = types[0]
            nargs = "+" if (nargs == "*" and default is EMPTY) else nargs
        elif origin is Literal:
            choices = [t.name if isinstance(t, Enum) else t for t in types]
            argtype = None  # create_literal_converter(types)
    if annotation == bool:
        action = "store_false" if default_bool else "store_true"
        argtype = None
    if isinstance(argtype, type) and issubclass(argtype, Enum):
        choices = list(getattr(argtype, "__members__").keys())
        argtype = None

    return action, nargs, argtype, choices


def __create_union_converter(types):

    try:
        if len(types) == 1 and issubclass(types[0], Enum):
            return types[0]
    except TypeError:
        if len(types) == 1 and isinstance(types[0], type):
            return types[0]

    def converter(value: str) -> Any:
        for t in types:
            try:
                if issubclass(t, Enum):
                    return t[value]
                # Attempt conversion
                while get_origin(t) is not None:
                    t = get_args(t)[0]
                converted_value = t(value)
                # Check string representation matches
                return converted_value
                # if str(converted_value) == value:
            except (ValueError, TypeError):
                continue  # Ignore and try the next type
        raise ValueError("ERRO")

    return converter


def __raise_caret_error(message: str):
    """Raise a caret-style RuntimeError pointing to the caller line."""
    # Get caller frame info
    stack = inspect.stack()
    frame = stack[2] if len(stack) > 2 else stack[1]
    filename = frame.filename
    lineno = frame.lineno
    assert frame.code_context is not None
    line = frame.code_context[0].rstrip("\n")
    col_start = frame.index or 0  # approximate, might be None

    # Create caret underline
    caret_line = " " * col_start + "^" * len(line.strip())

    # Format and print error with caret and message
    sys.stderr.write(f'  File "{filename}", line {lineno}\n')
    sys.stderr.write(f"    {line}\n")
    sys.stderr.write(f"    {caret_line}\n")
    sys.stderr.write(f"{type(RuntimeError()).__name__}: {message}\n")
    sys.exit(1)


##############################################################################################################
# %%          UNUSED FUNCTIONS
##############################################################################################################


def __create_literal_converter(types):
    def converter(s):
        for value in types:
            if isinstance(value, Enum) and s == getattr(value, "name"):
                return getattr(value, "name")
            if str(value) == s:
                return value
        raise ValueError("ERRO")

    return converter


def __count_leading_spaces(string: str):
    return len(string) - len(string.lstrip())


def __arg(
    *flags: str,
    make_flag: bool | None = None,
    group: ArgumentGroup | MutuallyExclusiveGroup | None = None,
    subparser: Field[Any] | None = None,
    **kwargs: Unpack[KeywordArguments],
) -> Any:
    """"""
    return field(
        default=kwargs.pop("default", None),
        metadata={
            "obj": ArgumentMetaData(
                flags=list(flags),
                make_flag=make_flag,
                group=group,
                dictionary=kwargs,
            ),
            "subparser": subparser,
        },
    )


def __get_metadata_from_field(field: Field[Any]) -> _ArgumentData:
    if type(field.type) == str:
        field.type = eval(field.type)
    data: _ArgumentData = _ArgumentData(name=field.name, typeannotation=field.type)
    if field.default is not field.default_factory:
        data.default = field.default
    if field.metadata:
        data.parser = field.metadata.get("subparser", None)
        metadata: ArgumentMetaData = field.metadata.get("obj", None)
        data.flags = metadata.flags
        data.make_flag = metadata.make_flag
        data.group = metadata.group
        data.kwargs = metadata.dictionary
    return data


##############################################################################################################
# %%          PUBLIC FUNCTIONS
##############################################################################################################

_main_command: Command | None = None


def command(func: Callable):
    global _main_command
    if _main_command is None:
        _main_command = Command(func)
        return func
    __raise_caret_error("The main command is already defined. Please use `clig.command()` function only once")


def subcommand(func: Callable):
    if _main_command is None:
        __raise_caret_error(
            "The main command is not defined. Please use `clig.subcommand()` function only after `clig.command()`"
        )
        raise
    _main_command.add_subcommand(func)
    return func


def data(
    *flags: str,
    make_flag: bool | None = None,
    group: ArgumentGroup | MutuallyExclusiveGroup | None = None,
    **kwargs: Unpack[KeywordArguments],
) -> ArgumentMetaData:
    return ArgumentMetaData(
        flags=list(flags),
        make_flag=make_flag,
        group=group,
        dictionary=kwargs,
    )


def run(func: Callable[..., Any] | None = None, args: Sequence[str] | None = None, **kwargs):
    if func is None:
        if _main_command is not None:
            return _main_command.run(args)
        __raise_caret_error("The main command is not defined. Please pass a function to `clig.run()`")
    return Command(func, **kwargs).run(args)
