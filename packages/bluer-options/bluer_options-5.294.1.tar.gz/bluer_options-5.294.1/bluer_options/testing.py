from typing import Any, List, Type

from bluer_options.logger import logger


def are_01(
    list_of_things: List[Any],
    log: bool = False,
) -> bool:
    return are_func_things(
        list_of_things,
        int,
        lambda x: x in (0, 1),
        "{} is neither 0 nor 1.",
        log=log,
    )


def are_nonempty_strs(
    list_of_things: List[Any],
    log: bool = False,
) -> bool:
    return are_func_things(
        list_of_things,
        str,
        bool,
        "empty str.",
        log=log,
    )


def are_positive_floats(
    list_of_things: List[Any],
    log: bool = False,
) -> bool:
    return are_func_things(
        list_of_things,
        float,
        lambda x: x > 0,
        "{:02f} < 0!",
        log=log,
    )


def are_positive_ints(
    list_of_things: List[Any],
    log: bool = False,
) -> bool:
    return are_func_things(
        list_of_things,
        int,
        lambda x: x > 0,
        "{} < 0!",
        log=log,
    )


def are_func_things(
    list_of_things: List[Any],
    type: Type,
    func,
    error_message: str,
    log: bool = False,
) -> bool:
    if not isinstance(list_of_things, list):
        if log:
            logger.error(f"{list_of_things.__class__.__name__} is not a list.")
        return False

    for thing in list_of_things:
        if not isinstance(thing, type):
            if log:
                logger.error(
                    "{}: {} expected, {} found.".format(
                        thing,
                        type,
                        thing.__class__.__name__,
                    )
                )
            return False

        if not func(thing):
            if log:
                logger.error(error_message.format(thing))

            return False

    return True


def is_list_of_str(thing: Any):
    return are_func_things(
        thing,
        str,
        lambda x: True,
        "you must never see this!",
    )
