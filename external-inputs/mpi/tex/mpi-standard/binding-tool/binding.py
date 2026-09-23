'''

'''


from typing import Mapping, MutableMapping
import copy
import logging
from collections import defaultdict


import common
from userfuncs import *


DEFAULT_ATTRIBUTES = {
        # validity attributes
        'lis_expressible': True,
        'c_expressible': True,
        'f08_expressible': True,
        'f90_expressible': True,

        'proxy_render': False,

        # TODO
        'f90_use_colons': False,
        # weird index overloading
        'f90_index_overload': None,
        'not_with_mpif': False,
        'f08_abstract_interface': True,
        'index_upper': False,
        'capitalized': False,

        # callback attributes
        'callback': False,
        'predefined_function': None,

        # semantic attributes
        'deprecated': False,
        'execute_once': False,

        # render binding as main definition
        'render_main': True,

        # control dependencies
        # 'needs_any': ['MPI_Init', 'MPI_Init_thread'],
        # 'needs_all': [],
        # 'leads_any': ['MPI_Finalize'],
        # 'leads_all': [],
    }


DEFAULT_TEMPORARIES = {
        'has_ierror': True,

        # whether this binding is from a definition
        'reference': None,

        # which expressible languages should be rendered
        # at definition mpi-binding
        'renders': ['lis', 'c', 'f08', 'f90'],

        'f90_overload_render': None,

        'render_main': True,
    }


def reset_parseset() -> None:
    """
    Resets the global variable PARSESET.
    """

    # global PARSESET
    # PARSESET = dict()
    PARSESET.clear()

    # name -> LIS/C/F08, name_f90 -> F90
    # these must be unique, otherwise you have big problems
    PARSESET['name'] = None
    PARSESET['name_f90'] = None

    # API attributes
    PARSESET['parameters'] = list()
    PARSESET['return_kind'] = None
    PARSESET['attributes'] = copy.deepcopy(DEFAULT_ATTRIBUTES)

    # not needed in apis.json
    PARSESET['temporaries'] = copy.deepcopy(DEFAULT_TEMPORARIES)


def parsing_done() -> None:
    """
    This hook is run after all the parsing is done for a given binding.
    """

    if PARSESET['temporaries']['has_ierror']:
        parameter('ierror',
                  'ERROR_CODE',
                  optional=True,
                  direction='out',
                  suppress='c_parameter lis_parameter')

    # default to an INT return type
    if PARSESET['return_kind'] is None:
        # MR this is not strictly true, Fortran just doesn't have a return type
        # since they are subroutines
        return_type('ERROR_CODE')


def execute_binding(binding: str, require_definition: bool = False) -> Mapping:
    '''
    Executes the content of a matched binding block.
    '''

    reset_parseset()

    logging.info("Rendering mpi-binding to LaTeX:")
    for line in binding.split('\n'):
        if line:
            logging.info('>> %s', line)

    # if definition required
    #     then ignore bindings without function_name
    if require_definition and 'function_name' not in binding:
        return None

    # execute the lines read from the mpi-binding
    # pylint: disable=exec-used
    try:
        exec(common.remove_unexpected_indentation(binding))
    except Exception as exception:
        print("Error processing binding " + common.remove_unexpected_indentation(binding))
        raise Exception

    parsing_done()

    # write to dataset
    logging.debug('parsed %s', PARSESET)
    parseset = copy.deepcopy(PARSESET)

    # clear parsed information
    logging.debug('clearing PARSESET: %s',
                  str(PARSESET))

    return parseset
