import numpy as np
from ttex.log.coco.postp.info import SuiteInfo
from cocopp.testbedsettings import Testbed, suite_to_testbed
import cocopp.testbedsettings as tbs
import cocopp.genericsettings as genericsettings


class TestbedSettings:
    def __init__(self, suite_info: SuiteInfo):
        self.suite_info = suite_info
        self.settings = TestbedSettings._create_settings_dict(suite_info)
        adapted_budget_factors = TestbedSettings._get_pprldistr_runlength_factors(
            min(suite_info.dimensions)
        )
        genericsettings.single_runlength_factors = adapted_budget_factors

    @staticmethod
    def spread_select(lst, k):
        """
        Select k values from lst, keeping first and last, spread evenly.

        Parameters:
            lst (list): original list of length n >= 2
            k (int): desired length, 2 <= k <= len(lst)

        Returns:
            list: downsampled list of length k
        """
        n = len(lst)
        if k >= n:
            return lst.copy()  # nothing to do
        if k < 2:
            raise ValueError("k must be at least 2 to keep first and last")

        # Compute indices spaced evenly from 0 to n-1
        indices = [round(i * (n - 1) / (k - 1)) for i in range(k)]

        return [lst[i] for i in indices]

    @staticmethod
    def _get_pprldistr_runlength_factors(min_dim: int):
        min_dim = max(
            min_dim, 1
        )  # Ignore 0 as it is treated as 1 in runlength postprocessing
        budget_factors = genericsettings.single_runlength_factors
        # remove all budget_factors where their product with min_dim is smaller
        # than 1 (i.e. the first recorded evaluation)
        budget_factors = [f for f in budget_factors if f * min_dim >= 1]
        return budget_factors

    @staticmethod
    def _create_settings_dict(
        suite_info: SuiteInfo, max_ppfigdim_targets: int = 5
    ) -> dict:
        suite_settings = dict(
            name=suite_info.name,
            instances_are_uniform=suite_info.instances_are_uniform,
            reference_algorithm_filename=suite_info.reference_algorithm_filename,
            reference_algorithm_displayname=suite_info.reference_algorithm_displayname,
            instancesOfInterest=suite_info.instancesOfInterest,
            data_format=suite_info.data_format,
            scenario=suite_info.scenario,
            number_of_points=suite_info.number_of_points,
        )
        dim_settings = dict(
            plots_on_main_html_page=[
                f"pprldmany_{dim}D_noiselessall.svg" for dim in suite_info.dimensions
            ],
            goto_dimension=min(
                suite_info.dimensions
            ),  # auto-focus on smallest dimension in html
            rldDimsOfInterest=suite_info.dimensions,
            dimensions_to_display=suite_info.dimensions,
        )
        first_func = min(info.func_id for info in suite_info.function_infos)
        last_func = max(info.func_id for info in suite_info.function_infos)
        fun_settings = dict(
            short_names={info.func_id: info.name for info in suite_info.function_infos},
            first_function_number=first_func,
            last_function_number=last_func,
            functions_with_legend=(first_func, last_func),
        )
        few_targets = [
            10**exp
            for exp in range(suite_info.max_target, suite_info.min_target - 1, -1)
        ]
        many_targets = [
            10**exp
            for exp in np.arange(
                suite_info.max_target, suite_info.min_target - 0.2, -0.2
            )
        ]
        target_settings = dict(
            pptable_ftarget=(
                10**suite_info.min_target
            ),  # value for determining the success ratio in all tables
            ppfvdistr_min_target=10**suite_info.min_target,
            pptable_targetsOfInterest=tuple(few_targets),
            ppfigdim_target_values=tuple(
                TestbedSettings.spread_select(few_targets, max_ppfigdim_targets)
            ),
            pprldistr_target_values=tuple(few_targets),
            pprldmany_target_values=tuple(many_targets),
            hardesttargetlatex=f"$10^{{{suite_info.min_target}}}$",
            pprldmany_target_range_latex=f"$10^{{[{suite_info.min_target}..{suite_info.max_target}]}}$",
        )
        settings = {**suite_settings, **dim_settings, **fun_settings, **target_settings}
        return settings


class TestbedFactory:
    @classmethod
    def create_testbed_class(cls, suite_info: SuiteInfo):
        settings = TestbedSettings(suite_info).settings
        class_name = f"CustomTestbed_{suite_info.name}"

        def __init__(self, target_values):
            for key, val in self.settings.items():
                setattr(self, key, val)
            self.instantiate_attributes(target_values)

        CustomTestbed = type(
            class_name,
            (Testbed,),
            {
                "__init__": __init__,
                "settings": settings,
            },
        )

        # Register the new testbed class in the suite_to_testbed mapping
        suite_to_testbed[suite_info.name] = class_name
        # Inject new class into cocopp namespace so it is available there
        setattr(tbs, class_name, CustomTestbed)

        return CustomTestbed
