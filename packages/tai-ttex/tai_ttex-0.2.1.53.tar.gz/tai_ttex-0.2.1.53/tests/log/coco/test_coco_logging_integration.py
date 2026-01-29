# integration test for coco logging
import os.path as osp
import cocopp
from ttex.log.coco import (
    COCOStart,
    COCOEval,
    COCOEnd,
)
import numpy as np
from cocopp.pproc import DictAlg
import shutil
import pytest
from ttex.log.utils.coco_logging_setup import teardown_coco_logger, setup_coco_logger
from tests.log.coco.postp.test_testbed import create_testbedsettings
from ttex.log.coco.postp.testbed import TestbedFactory
from ttex.log.coco.postp.info import SuiteInfo


def get_dummy_start_params(
    suite: SuiteInfo,
    problem_idx: int,
    dim_idx: int,
    inst: int,
) -> dict:
    func_info = suite.function_infos[problem_idx]
    return_dict = {
        "fopt": np.random.randn() * 100,
        "algo": "test_algo",
        "problem": func_info.func_id,
        "dim": func_info.dims[dim_idx],
        "inst": inst,
        "suite": suite.name,
        "exp_id": "test_exp_id",
    }
    return return_dict


def generate_events(
    num_evals: int,
    suite: SuiteInfo,
    problem_idx: int,
    dim_idx: int,
    inst: int,
):
    events = []
    return_dict = get_dummy_start_params(suite, problem_idx, dim_idx, inst)
    start_record = COCOStart(**return_dict)
    events.append(start_record)
    for _ in range(num_evals):
        curr_dim = start_record.dim
        x = np.random.rand(curr_dim)
        mf = np.random.rand() + start_record.fopt
        events.append(COCOEval(x=x.tolist(), mf=mf))
    events.append(COCOEnd())
    return events


@pytest.fixture(scope="function", autouse=True)
def cleanup_dummy_files():
    shutil.rmtree("test_exp_id", ignore_errors=True)
    shutil.rmtree("test_dir", ignore_errors=True)

    yield

    shutil.rmtree("test_dir", ignore_errors=True)
    shutil.rmtree("test_exp_id", ignore_errors=True)


def simulate_once(
    logger,
    num_evals: int,
    suite: SuiteInfo,
    problem_idx: int = 0,
    dim_idx: int = 0,
    inst: int = 2,
):
    events = generate_events(num_evals, suite, problem_idx, dim_idx, inst)
    for event in events:
        logger.info(event)

    return events[0]  # return start record for further checks


def check_files_exist(start_record: COCOStart):
    for type_str in ["info", "log_dat", "log_tdat"]:
        # Check if the dummy files are deleted
        filepath = osp.join("test_dir", f"coco_{type_str}.txt")
        assert not osp.exists(filepath), f"{type_str} dummy log file retained"
    # Check if the log files are created
    log_file_base = osp.join(
        f"{start_record.exp_id}",
        f"{start_record.suite}",
        f"{start_record.algo}",
        f"data_{start_record.problem}",
        f"f{start_record.problem}_d{start_record.dim}_i{start_record.inst}",
    )
    assert osp.exists(f"{log_file_base}.dat"), "COCO dat log file not created"
    assert osp.exists(f"{log_file_base}.tdat"), "COCO tdat log file not created"
    # Check that tdat file has at least one record (more than just header)
    with open(
        f"{log_file_base}.tdat",
        "r",
    ) as f:
        lines = f.readlines()
        assert len(lines) > 1, "COCO tdat log file is empty"

    assert osp.exists(
        osp.join(
            f"{start_record.exp_id}",
            f"{start_record.suite}",
            f"{start_record.algo}",
            f"f{start_record.problem}_i{start_record.inst}.info",
        )
    ), "COCO info file not created"


def test_coco_logging_integration():
    _, suite_info = create_testbedsettings()
    TestbedFactory.create_testbed_class(suite_info)

    logger = setup_coco_logger("coco_logger1")

    to_simulate = [
        {"num_evals": 50, "problem_idx": 0, "dim_idx": 2, "inst": 2},
        {"num_evals": 30, "problem_idx": 0, "dim_idx": 2, "inst": 3},
        {"num_evals": 30, "problem_idx": 0, "dim_idx": 3, "inst": 4},
        {"num_evals": 30, "problem_idx": 1, "dim_idx": 2, "inst": 2},
    ]
    start_records = [None] * len(to_simulate)
    for i, sim_vals in enumerate(to_simulate):
        start_records[i] = simulate_once(
            logger,
            num_evals=sim_vals["num_evals"],
            suite=suite_info,
            problem_idx=sim_vals["problem_idx"],
            dim_idx=sim_vals["dim_idx"],
            inst=sim_vals["inst"],
        )

    # Close handlers and remove from logger
    teardown_coco_logger("coco_logger1")  # Ensure handlers are closed
    # Check files exist for first start record
    for start_rec in start_records:
        assert isinstance(start_rec, COCOStart)
        check_files_exist(start_rec)
    ## check with cocopp
    res = cocopp.main(
        f"-o test_exp_id/ppdata test_exp_id/{start_records[0].suite}/test_algo"
    )
    assert isinstance(res, DictAlg)
    result_list = res[("test_algo", "")]
    # count different scenarios in to_simulate (different problem idx and dim idx combinations)
    conv_to_sim = [
        {
            "prob": suite_info.function_infos[to_sim["problem_idx"]].func_id,
            "dim": suite_info.function_infos[to_sim["problem_idx"]].dims[
                to_sim["dim_idx"]
            ],
            "inst": to_sim["inst"],
        }
        for to_sim in to_simulate
    ]
    scenario_combs = [
        (to_sim["problem_idx"], to_sim["dim_idx"]) for to_sim in to_simulate
    ]
    assert len(result_list) == len(set(scenario_combs))
    found_to_sim = []
    for res_dict in result_list:
        assert res_dict.algId == "test_algo"
        for inst in res_dict.instancenumbers:
            res = {"problem": res_dict.funcId, "dim": res_dict.dim, "inst": inst}
            # Find corresponding entry in conv_to_sim
            for i, to_sim in enumerate(conv_to_sim):
                if (
                    to_sim["prob"] == res["problem"]
                    and to_sim["dim"] == res["dim"]
                    and to_sim["inst"] == res["inst"]
                ):
                    found_to_sim.append(i)
                    break
    assert len(found_to_sim) == len(to_simulate)


def test_coco_logging_integration_no_dim_inst():
    _, suite_info = create_testbedsettings()
    TestbedFactory.create_testbed_class(suite_info)
    logger = setup_coco_logger("coco_logger2")
    start_record = simulate_once(
        logger, num_evals=20, suite=suite_info, problem_idx=2, dim_idx=0, inst=0
    )
    # Close handlers and remove from logger
    teardown_coco_logger("coco_logger2")  # Ensure handlers are closed
    # Check files exist for first start record
    assert isinstance(start_record, COCOStart)
    check_files_exist(start_record)

    res = cocopp.main(f"-o test_exp_id/ppdata test_exp_id/{suite_info.name}/test_algo")
    assert isinstance(res, DictAlg)
