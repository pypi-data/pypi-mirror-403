from ttex.log.coco.run_cocopp import run_cocopp
from ttex.log.coco.postp.info import FunctionInfo, SuiteInfo
import pytest
import shutil


def test_run_cocopp():
    # This is a placeholder test to ensure run_cocopp can be called without errors.
    # In a real test, you would provide actual result paths and a SuiteInfo object.
    result_paths = ["path/to/result1", "path/to/result2"]

    # Create a dummy SuiteInfo object for testing
    func_infos = [
        FunctionInfo(1, "f1", "Sphere Function", dims=[2, 3]),
        FunctionInfo(2, "f2", "Rosenbrock Function", dims=[3, 5]),
    ]
    suite_info = SuiteInfo(name="TestSuite", function_infos=func_infos)

    with pytest.raises(Exception) as excinfo:
        run_cocopp(result_paths, suite_info, silent=True)
    assert excinfo.type is ValueError
    assert (
        "seems not to be an existing file or match any archived data"
        in excinfo.value.args[0]
    )

    # Remove ppdata folder
    shutil.rmtree("ppdata", ignore_errors=True)
