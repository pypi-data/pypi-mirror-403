from ttex.log.coco.postp.info import FunctionInfo, SuiteInfo


def test_f_info():
    f_info = FunctionInfo(1, "f1", "Sphere Function")
    assert f_info.func_id == 1
    assert f_info.name == "f1"
    assert f_info.long_name == "Sphere Function"
    assert f_info.to_str(short=True) == "1 f1"
    assert f_info.to_str(short=False) == "1 Sphere Function"


def create_suite_info():
    func_infos = [
        FunctionInfo(1, "f1", "Sphere Function", dims=[2, 3, 10, 20]),
        FunctionInfo(2, "f2", "Rosenbrock Function", dims=[3, 5, 6, 9]),
        FunctionInfo(3, "f3", "Changing dims"),
    ]
    suite_info = SuiteInfo(name="TestSuite", function_infos=func_infos)
    return suite_info


def test_suite_Info():
    suite_info = create_suite_info()
    func_infos = suite_info.function_infos

    assert suite_info.name == "TestSuite"
    assert suite_info.dimensions == [1, 2, 3, 5, 6, 9, 10, 20]
    assert suite_info.function_infos == func_infos
    assert suite_info.number_of_points == 5
    assert suite_info.max_target == 2
    assert suite_info.min_target == -8
