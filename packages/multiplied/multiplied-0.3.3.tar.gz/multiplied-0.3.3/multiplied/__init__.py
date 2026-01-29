#!bin/python3

from pathlib import Path
import toml


# -- core -----------------------------------------------------------

##########################################################
# explicit order: map -> matrix -> template -> algorithm #
##########################################################


from .core.map import (
    Map,
    build_dadda_map,
    empty_map,
)

from .core.matrix import (
    Matrix,
    Slice,
    build_matrix,
    empty_rows,
)


from .core.template import (
    Pattern,
    Template,
    build_csa,
    build_adder,
    resolve_pattern,
    checksum,
)

from .core.algorithm import (
    Algorithm,
    isolate_arithmetic_units,
)

from .core.truth import (
    truth_scope,
    truth_table,
    shallow_truth_table,
)


# -- utils ----------------------------------------------------------

from .core.utils.char import (
    ischar,
    chargen,
    chartff,
    allchars,
)


from .core.utils.pretty import (
    pretty,
    mprint,
)

# -- datasets -------------------------------------------------------



# -- io -------------------------------------------------------------

from .io.lazy_json import (
    json_pretty_store,
)

# from .io.parquet import()
#


# -- External -------------------------------------------------------


# -- Tests ----------------------------------------------------------

# from .tests.test_population import (
#     test_pop_empty_matrix,
#     test_pop_build_matrix,
#     test_pop_agorithm,
# )

# from .tests.test_templates import (
#    test_temp_build_csa4,
#    test_temp_build_csa8,
#    test_temp_build_adder4,
#    test_temp_build_adder8,
# )

# from .tests.test_to_json import (
#     test_to_json4,
#     test_to_json8,
# )



# -- pyproject.toml metadata ----------------------------------------


with open(Path(__file__).parent.parent / "pyproject.toml", "r") as f:
    MP_TOML = toml.loads(f.read())

MP_VERSION = MP_TOML["project"]["version"]

SUPPORTED_BITWIDTHS = {4, 8}


# -- __all__ --------------------------------------------------------

__all__ = [
    'Matrix',
    'Slice',
    'build_matrix',
    'empty_rows',
    'Pattern',
    'Template',
    'Algorithm',
    'isolate_arithmetic_units',
    'build_dadda_map',
    'empty_map',
    'build_csa',
    'build_adder',
    'resolve_pattern',
    'checksum',
    'truth_scope',
    'shallow_truth_table',
    'truth_table',
    'json_pretty_store',
    'Map',
    'ischar',
    'chargen',
    'chartff',
    'allchars',
    'pretty',
    'mprint',
    'MP_VERSION',
    'SUPPORTED_BITWIDTHS',

]
