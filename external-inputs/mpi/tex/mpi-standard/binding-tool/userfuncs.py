"""
Holds all functions that can be called from the MPI Standard
mpi-binding blocks.
"""


from typing import MutableMapping, Optional, Iterable
import logging
import sys


import bindingtypes


VALID_DIRECTIONS = ["in", "inout", "out"]


PARSESET: MutableMapping = {}


def return_type(kind: str) -> None:
    """
    Define return type for current parsing PARSESET.

    If this function is not invoked, the current PARSESET defaults to
    return_type('ERROR_CODE').
    """

    logging.debug("found return type statement %s", kind)

    if PARSESET["return_kind"] is not None:
        raise RuntimeError("Return type already defined.")

    PARSESET["return_kind"] = kind


def function_name(name: str, name_f90: str = None, capitalized: bool = False) -> None:
    """
    Define the function name for the current parsing PARSESET.

    Cannot be used with render(name, languages).
    """

    if not name:
        raise RuntimeError("No name given to function_name.")

    if "name" in PARSESET and PARSESET["name"]:
        raise RuntimeError("Function name already defined in " "function_name command.")

    logging.debug("Function name %s", name)

    PARSESET['name'] = name
    PARSESET['name_f90'] = name_f90
    PARSESET['attributes']['capitalized'] = capitalized
    PARSESET['temporaries']['render_main'] = True


def render(name: str, languages: str, nomain = False) -> None:
    """
    Mark this binding as a reference render for the name and language.

    Cannot be used with function_name(name).
    """

    languages = [language.strip() for language in languages.split(",")]

    if not name:
        raise RuntimeError("No name given to a render command.")

    if PARSESET["name"]:
        raise RuntimeError("Function name already defined in render command.")

    for language in languages:
        if language not in ("lis", "c", "f08", "f90"):
            raise RuntimeError(
                f"Unrecognized language in render statement " f'"{language}".'
            )

    PARSESET['temporaries']['reference'] = name.lower()
    PARSESET['temporaries']['renders'] = languages
    PARSESET['temporaries']['render_main'] = not nomain

def no_render(languages: str) -> None:
    """
    Marks the binding to not render latex bindings where it is defined.
    """

    languages = [language.strip() for language in languages.split(",")]

    logging.debug("this binding is not rendering bindings for %s", " ".join(languages))

    for language in languages:
        PARSESET["temporaries"]["renders"].remove(language)


def render_nomain() -> None:
    """
    Prevent a rendered block from emitting a main definition.
    """
    #print("RENDER NOMAIN")
    PARSESET['temporaries']['render_main'] = False
    #print(PARSESET)

def parameter(
    name: str,
    kind: str,
    *,
    desc: str = "",
    # TODO convert direction to ENUM
    direction: str = "in",
    length: Optional[str] = None,
    func_type: str = "",  # Only valid for FUNCTION parameters
    array_type: str = "",
    pointer: Optional[bool] = None,
    constant: bool = False,
    root_only: bool = False,
    asynchronous: bool = False,  # Whether MPI "owns" this data after
    # procedure returns
    suppress: str = "",  # Possible values: f08_intent (i.e.,
    # suppress emiting the F08 INTENT clause),
    # lis_paren (i.e., suppress the
    # parenthentical that is usually generated
    # after the LIS description)
    optional: bool = False,
    large_only: bool = False,
) -> None:
    """
    Append a parameter to the current parsing PARSESET.

    Note that MPI-3.1 2.3 p10:23-27 differentiates between the
    "direction" for the language independent specification and the
    C/Fortran bindings in one special case: if the parameter is an
    opaque handle and the direction is IN or INOUT, that only refers
    to the fact that the MPI *object* is modified -- it does not
    necessarily mean that the MPI *handle* (i.e., the passed
    parameter) is modified.  Hence, while in most cases the LIS
    direction is the same as the param direction, we need to have the
    ability to make them different.

    The "direction" parameter can therefore be:

    <empty> : defaults to "in"
    "in"    : IN for both LIS and language-specific bindings
    "out"   : OUT for both LIS and language-specific bindings
    "inout" : INOUT for both LIS and language-specific bindings
    "lis:DIR1,param:DIR2" : DIR1 for the LIS and DIR2 for the
        language-specific bindings

    """

    if not name or not kind:
        raise ValueError('Fields "name" or "kind" cannot be empty.')

    if func_type and kind not in ("FUNCTION", "POLYFUNCTION", "FUNCTION_SMALL"):
        raise ValueError(
            ("The func_type attribute is only valid for FUNCTION " "parameters.")
        )

    if kind == "FUNCTION" and not func_type:
        raise ValueError(
            ("The FUNCTION parameter requires that func_type is " "specified.")
        )

    if kind == "STRING_2DARRAY" and not length:
        raise ValueError(
            ("The STRING_2DARRAY parameter requires that length " "is specified.")
        )

    if kind not in bindingtypes.LIS_KIND_MAP:
        sorted_lis = "\n".join(sorted(bindingtypes.LIS_KIND_MAP.keys()))
        raise ValueError(
            (f'Invalid parameter type ("{kind}") -- valid types ' f"are: {sorted_lis}")
        )

    # Handle the different cases for direction (i.e., where the
    # direction is the same for both LIS and the language-specific
    # bindings, and where the direction is different between the LIS
    # and the language-specific bindings).
    direction = direction.lower()
    if direction in VALID_DIRECTIONS:
        lis_direction = direction
        param_direction = direction

    else:
        for entry in direction.split(","):
            thing, direction = entry.split(":")
            if direction not in VALID_DIRECTIONS:
                logging.critical("Unrecognized direction: %s.", direction)
                sys.exit(1)

            if thing == "lis":
                lis_direction = direction

            elif thing == "param":
                param_direction = direction

            else:
                sys.stderr.write(
                    "Unrecognized direction type: {thing}".format(thing=thing)
                )
                sys.exit(1)

    data = {
        "name": name,
        "kind": kind,
        "desc": desc,
        "lis_direction": lis_direction,
        "param_direction": param_direction,
        "length": length,
        "func_type": func_type,
        "array_type": array_type,
        "pointer": pointer,
        "constant": constant,
        "root_only": root_only,
        "asynchronous": asynchronous,
        "suppress": suppress.lower(),
        "optional": optional,
        "large_only": large_only,
    }

    logging.debug("found parameter dict definition %s.", str(data))

    PARSESET["parameters"].append(data)


def construct_mpit_string_parameters(name: str, category: str) -> None:
    """
    Constructs two parameter calls from the given string information.
    """

    parameter(
        name,
        "STRING",
        desc=(
            f"buffer to return the string containing the {name} " f"of the {category}"
        ),
        direction="out",
    )

    parameter(
        f"{name}_len",
        "STRING_LENGTH",
        desc=(f"length of the string and/or buffer for " f"\\mpiarg{{{name}}}"),
        direction="inout",
    )


def no_ierror() -> None:
    """
    For the small number of MPI functions that do not have an ierror
    argument.
    """

    logging.debug("no ierror for this procedure")
    PARSESET["temporaries"]["has_ierror"] = False


def no_lis_binding() -> None:
    """
    Marks this API to not have an LIS expression.
    """
    logging.debug("no LIS binding for this procedure")
    PARSESET["attributes"]["lis_expressible"] = False

    no_render("lis")


def no_c_binding() -> None:
    """
    Marks this API to not have a C expression.
    """

    logging.debug("no C binding for this procedure")
    PARSESET["attributes"]["c_expressible"] = False

    no_render("c")


def no_f08_binding(proxy_render: bool = False) -> None:
    """
    Marks this API to not have an F08 expression.
    """

    logging.debug("no F08 binding for this procedure")
    PARSESET["attributes"]["f08_expressible"] = False

    if proxy_render:
        PARSESET["attributes"]["proxy_render"] = proxy_render

    else:
        no_render("f08")


def no_f90_binding() -> None:
    """
    Marks this API to not have an F90 expression.
    """

    logging.debug("no F90 binding for this procedure")
    PARSESET["attributes"]["f90_expressible"] = False

    no_render("f90")


def f90_use_colons() -> None:
    """
    Use F08-style :: between types and dummy parameters
    """

    logging.debug("use F08-style :: in the F90 rendering for this procedure")
    PARSESET["attributes"]["f90_use_colons"] = True


def callback() -> None:
    """
    Mark this binding as a callback.
    """

    logging.debug("this binding is a callback")
    PARSESET["attributes"]["callback"] = True


def deprecate() -> None:
    """
    Mark this binding as deprecated.
    """

    logging.debug("this binding is deprecated.")
    PARSESET["attributes"]["deprecated"] = True


def predefined_function(callback_name: str) -> None:
    """
    Marks this function as a predefined function of type
    of the callback function.
    """

    logging.debug("this binding is a predefined function for %s", callback_name)
    PARSESET["attributes"]["predefined_function"] = callback_name


def f90_overload(text: str) -> None:
    """
    This is a simple hack to achieve the 5 mpifoverload statements.
    """

    logging.debug("this binding contains a mpifoverload statement.")

    PARSESET["attributes"]["f90_index_overload"] = text


def f90_overload_render(interface_name: str) -> None:
    """
    Render the f90_overload text here.
    """

    logging.debug("render f90_overload text here")

    PARSESET["temporaries"]["f90_overload_render"] = interface_name
    PARSESET["temporaries"]["renders"] = []


def not_with_mpif():
    """
    Marks this interface as not being available through the mpif.h file.
    """

    logging.debug("this binding is not available in mpif.h")

    PARSESET["attributes"]["not_with_mpif"] = True


def not_abstract_interface():
    """
    Marks this interface as not being a Fortran 2008 abstract interface, but
    an explicitly named MPI interface. This causes two Fortran 2008 functions
    to be emitted, one with the postfix attached.
    """

    logging.debug("this binding is not an abstract interface")

    PARSESET["attributes"]["f08_abstract_interface"] = False


def with_uppercase_index():
    """
    Marks this interface to contain an UPPERCASE binding index.
    """

    logging.debug("this binding has an uppercase index.")

    PARSESET["attributes"]["index_upper"] = True
