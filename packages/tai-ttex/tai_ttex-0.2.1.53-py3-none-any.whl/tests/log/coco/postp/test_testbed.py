from ttex.log.coco.postp.testbed import TestbedSettings, TestbedFactory
import numpy as np
from cocopp.testbedsettings import Testbed, get_testbed_from_suite
import importlib
from tests.log.coco.postp.test_info import create_suite_info
import pytest


def create_testbedsettings():
    suite_info = create_suite_info()
    testbed_settings = TestbedSettings(suite_info)
    return testbed_settings, suite_info


def test_set_genericsettings():
    import cocopp.genericsettings as genericsettings

    original_settings = genericsettings.single_runlength_factors.copy()
    testbed_settings, suite_info = create_testbedsettings()
    adapted_budget_factors = TestbedSettings._get_pprldistr_runlength_factors(
        min(suite_info.dimensions)
    )

    assert genericsettings.single_runlength_factors == adapted_budget_factors

    # Reset to original settings
    genericsettings.single_runlength_factors = original_settings


def test_testbed_settings():
    testbed_settings, suite_info = create_testbedsettings()
    settings = testbed_settings.settings

    assert settings["name"] == "TestSuite"
    assert settings["instances_are_uniform"] is False
    assert settings["reference_algorithm_filename"] is None
    assert settings["reference_algorithm_displayname"] is None
    assert settings["instancesOfInterest"] is None
    assert settings["data_format"] == suite_info.data_format
    assert settings["scenario"] == "rlbased"

    dims = suite_info.dimensions

    assert settings["plots_on_main_html_page"] == [
        f"pprldmany_{dim}D_noiselessall.svg" for dim in dims
    ]

    assert settings["goto_dimension"] == min(dims)
    assert settings["rldDimsOfInterest"] == dims
    assert settings["dimensions_to_display"] == dims

    assert settings["short_names"] == {1: "f1", 2: "f2", 3: "f3"}
    assert settings["first_function_number"] == 1
    assert settings["last_function_number"] == 3
    assert settings["functions_with_legend"] == (1, 3)

    few_targets = [
        10**exp for exp in range(suite_info.max_target, suite_info.min_target - 1, -1)
    ]
    many_targets = [
        10**exp
        for exp in np.arange(suite_info.max_target, suite_info.min_target - 0.2, -0.2)
    ]

    assert settings["pptable_ftarget"] == 10**suite_info.min_target
    assert settings["ppfvdistr_min_target"] == 10**suite_info.min_target
    assert settings["pptable_targetsOfInterest"] == tuple(few_targets)
    assert len(settings["ppfigdim_target_values"]) == 5
    assert settings["pprldistr_target_values"] == tuple(few_targets)
    assert settings["pprldmany_target_values"] == tuple(many_targets)


def test_testbed_factory():
    testbed_settings, suite_info = create_testbedsettings()
    testbed_class = TestbedFactory.create_testbed_class(suite_info)
    class_name = testbed_class.__name__

    assert hasattr(testbed_class, "settings")
    assert testbed_class.settings == testbed_settings.settings
    assert issubclass(testbed_class, Testbed)

    assert get_testbed_from_suite(suite_info.name) == class_name

    # try importing from cocopp
    module = importlib.import_module("cocopp.testbedsettings")
    cls = getattr(module, class_name)
    assert cls == testbed_class


def test_spread_select():
    lst = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    k = 4
    new_list = TestbedSettings.spread_select(lst, k)
    assert len(new_list) == k
    assert lst[0] in new_list
    assert lst[-1] in new_list
    for item in new_list:
        assert item in lst


@pytest.mark.parametrize("dim", [0, 1])
def test_get_pprl_dist_runlength_factors(dim):
    budget_factors = TestbedSettings._get_pprldistr_runlength_factors(dim)
    # Check that all budget factors are larger than 0
    for factor in budget_factors:
        assert factor > 0
