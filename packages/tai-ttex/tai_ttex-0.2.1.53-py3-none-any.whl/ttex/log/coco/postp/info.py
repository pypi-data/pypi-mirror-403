from dataclasses import dataclass
from typing import List
from cocopp.dataformatsettings import BBOBNewDataFormat
from typing import Optional


class FunctionInfo:
    def __init__(
        self, func_id: int, name: str, long_name: str, dims: Optional[List[int]] = None
    ):
        self.func_id = func_id
        self.name = name
        self.long_name = long_name
        self.dims = dims if dims is not None else [0]

    def to_str(self, short: bool = False) -> str:
        if short:
            return f"{self.func_id} {self.name}"
        else:
            return f"{self.func_id} {self.long_name}"


@dataclass
class SuiteInfo:
    name: str
    function_infos: List[FunctionInfo]
    number_of_points = 5  # number of points in log-scale plots (per decade)
    max_target = 2  # exponent of maximum target value for postprocessing
    min_target = -8  # exponent of minimum target value for postprocessing
    scenario = "rlbased"

    def __post_init__(self):
        assert (
            len(self.function_infos) > 0
        ), "function_infos must contain at least one FunctionInfo"
        # defaults based on ttex implementation
        self.instances_are_uniform = False
        self.reference_algorithm_filename = None
        self.reference_algorithm_displayname = None
        self.instancesOfInterest = None  # None: consider all instances
        self.data_format = BBOBNewDataFormat()

        all_dims = [dim for info in self.function_infos for dim in info.dims]
        # replace 0 with 1 to avoid having 0 dimensions in postp
        all_dims = [1 if dim == 0 else dim for dim in all_dims]
        self.dimensions = sorted(list(set(all_dims)))
