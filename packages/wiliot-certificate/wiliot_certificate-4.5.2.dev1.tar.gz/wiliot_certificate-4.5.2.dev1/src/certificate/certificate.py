
# generic
import sys
import os
sys.path.insert(0, os.path.abspath(".."))
import webbrowser
import glob
import datetime
import tabulate
import threading
import traceback
import shutil
import re
import time
# Local imports
from certificate.wlt_types import *
from certificate.cert_defines import *
import certificate.cert_prints as cert_prints
import certificate.cert_utils as cert_utils
import certificate.cert_results as cert_results
import certificate.cert_gw_sim as cert_gw_sim
import certificate.cert_mqtt as cert_mqtt

TEST_LIST_FW_UPDATE_FILE = "ut/fw_update_test_list.txt"
TESTER_VALIDATION_SCHEMA_PATH = os.path.join(BASE_DIR, "../common/utils/tester_validation_schema.json")

os.system('')

def filter_tests(test_list, run, drun):
    test_lines = [l.strip() for l in open(os.path.join(BASE_DIR, test_list)).readlines() if l.strip() and not l.strip().startswith("#")]
    if run:
        test_lines = [tl for tl in test_lines if re.search(run, tl.strip().split()[0])]
    if drun:
        test_lines = [tl for tl in test_lines if not re.search(drun, tl.strip().split()[0])]
    return test_lines


def skip_test_check(test, validation_schema):
    skip_string = ""
    if test.multi_brg and (not cert_utils.brg_flag(validation_schema) or not test.active_brg):
        skip_string = f"Skipped {test.module_name} multi brg test because device under test isn't a bridge"
    elif test.multi_brg and not test.brg1:
        skip_string = f"Skipped {test.module_name} multi brg test because brg1 wasn't given"
    # TODO - check if module is supported by the bridge in the validation schema
    elif test.active_brg and not test.active_brg.is_sup_cap(test):
        skip_string = f"Skipped {test.module_name} because {cert_utils.module_name_id2py(test.test_module)} module is not supported"
    # TODO - check if module is supported by the bridge in the validation schema
    elif test.active_brg and ag.MODULE_EXT_SENSORS not in test.active_brg.sup_caps and "signal_indicator" in test.name:  
        skip_string = f"Skipped signal indicator tests because they are not supported when external sensors module not supported"
    elif test.data != DATA_SIMULATION and test.test_json[DATA_SIMULATION_ONLY_TEST]:
        skip_string = f"Skipped {test.module_name} because it can run only with data simulation mode"
    elif GW_ONLY_TEST in test.test_json and test.test_json[GW_ONLY_TEST] and test.dut_is_bridge():
        skip_string = f"Skipped {test.module_name} because it can run only with Gateway or Combo devices"
    elif BRIDGE_ONLY_TEST in test.test_json and test.test_json[BRIDGE_ONLY_TEST] and not test.dut_is_bridge():
        skip_string = f"Skipped {test.module_name} because it can run only with Bridge devices without Gateway functionality"
    elif SUPPORTED_FROM_API_VERSION in test.test_json:
        if test.test_json[MODULE] == "Cloud Connectivity" and test.dut_is_gateway() and int(test.dut.gw_api_version) < test.test_json[SUPPORTED_FROM_API_VERSION]:
            skip_string = f"Skipped {test.module_name} because it is supported from api version {test.test_json[SUPPORTED_FROM_API_VERSION]} and dut api version is {test.dut.gw_api_version}"
        elif test.test_json[MODULE] != "Cloud Connectivity" and test.active_brg.api_version < test.test_json[SUPPORTED_FROM_API_VERSION]:
            skip_string = f"Skipped {test.module_name} because it is supported from api version {test.test_json[SUPPORTED_FROM_API_VERSION]} and dut api version is {test.active_brg.api_version}"
    if skip_string:
        cert_prints.wlt_print(f"{cert_prints.SEP}{skip_string}{cert_prints.SEP}", "WARNING")
        test.reason = skip_string
        test.rc = TEST_SKIPPED
    return test

def clean(args):
    if args.clean:
        cert_prints.wlt_print(os.getcwd())
        for dir in glob.glob('**/cert_artifacts_*/', recursive=True):
            cert_prints.wlt_print(f"Removing folder: {dir}")
            shutil.rmtree(dir)

def main(args):
    # Clean
    clean(args)

    # Create main text log
    cert_prints.init_logging(log_level=args.log_level, mqtt_level=cert_prints.INFO)
    
    args.tester = cert_utils.get_tester_id(args.tester)
    if ':' in args.dut:
        args.dut, args.combo_ble_addr = args.dut.split(':')

    cert_prints.wlt_print(f"wiliot_certificate version: {CERT_VERSION}")
    cert_prints.wlt_print(str(args.__dict__))
    start_time = datetime.datetime.now()

    # Filter tests
    test_list = TEST_LIST_FW_UPDATE_FILE if args.latest or args.rc else args.tl
    test_lines = filter_tests(test_list=test_list, run=args.run, drun=args.drun)
    if args.max_output_power is None and any(["signal_indicator" in l for l in test_lines]):
        cert_utils.handle_error("\nERROR: max_output_power is required when running signal indicator tests!", start_time)

    # JSON validation schema basic validation
    validation_schema = cert_utils.load_and_validate_schema(args.validation_schema, start_time, api_version=args.api_version)

    # Init mqtt client for tester
    tester_mqttc = cert_mqtt.mqttc_init(args.tester, args.custom_broker, data=args.data, target=TESTER)

    # Init mqtt client for device under test when it is cloud connectivity bridge
    if cert_utils.cloud_connectivity_flag(validation_schema) and args.dut != args.tester:
        dut_mqttc = cert_mqtt.mqttc_init(args.dut, args.custom_broker, data=args.data, target=DUT)
    else:
        # Use the same mqtt client of the tester if device under test is a bridge only
        dut_mqttc = tester_mqttc

    # Prepare tester
    gw_sim_thread = None
    if GW_SIM_PREFIX in args.tester:
        # Run Gateway Simulator in separate thread
        gw_sim_thread = threading.Thread(target=cert_gw_sim.gw_sim_run, daemon=True, kwargs={'port':args.port, 'gw_id': args.tester,
                                                                                             'custom_broker':args.custom_broker,
                                                                                             'disable_interference_analyzer':args.disable_interference_analyzer})
        gw_sim_thread.start()
        sleep_time = (len(cert_gw_sim.CHANNELS_TO_ANALYZE) * 30) + 15 if not args.disable_interference_analyzer else 10
        time.sleep(sleep_time)
    # Load and validate tester's validation schema
    tester_validation_schema = cert_utils.load_and_validate_schema(TESTER_VALIDATION_SCHEMA_PATH, start_time, tester=True)
    tester = cert_utils.prep_tester(args, tester_mqttc, start_time, tester_validation_schema, gw_sim_thread)
    
    # Prepare device under test
    dut = cert_utils.prep_dut(args, tester, validation_schema, dut_mqttc, start_time, args.agg, args.gw_api_version)

    # Prepare second bridge (brg1) if given
    brg1 = None
    if args.brg1:
        # Assume an extra bridge is of the same type as the DUT and use the same validation schema
        brg1 = cert_utils.ut_prep_brg(args, start_time, tester, args.brg1, validation_schema=validation_schema['modules'])

    # Collecting the tests
    tests = []
    for tl in test_lines:
        test = cert_utils.WltTest(tl, tester, dut, brg1=brg1, exit_on_param_failure=args.exit_on_param_failure,
                       latest=args.latest, release_candidate=args.rc, sterile_run=args.sterile_run, data=args.data,
                       ci_cd=args.ci_cd, send_hb_before_sim=args.send_hb_before_sim)
        tests += [test]

    # Running the tests
    cert_prints.wlt_print(cert_prints.SEP)
    cert_prints.wlt_print("\n - ".join([f"\nRunning {len(tests)} tests:"] + [t.name if not t.internal_brg else f"{t.name} (internal brg)" for t in tests]))

    failures, skipped = 0, 0
    exit_on_test_failure = args.exit_on_test_failure
    i = 0

    for i, test in enumerate(tests):
        test = skip_test_check(test, validation_schema)
        if test.rc == TEST_SKIPPED:
            for phase in test.phases:
                phase.rc = TEST_SKIPPED
                if test.reason:
                    test.add_phase_reason(phase.name, test.reason)
            skipped += 1
        else:
            try:
                test_module_name = cert_utils.load_module(f'{test.module_name}.py', f'{test.dir}/{test.module_name}.py')
                test = cert_prints.start_test_logs(test, dut_mqtt_exist = dut_mqttc != tester_mqttc)
                test = test_module_name.run(test)
            except Exception as e:
                cert_prints.wlt_print(traceback.format_exc(), log_level=cert_prints.ERROR, to_text=True, to_console=True)
                test.add_phase_reason(RESTORE_CONFIG, f"Exception occurred: {e!r}")
                test.rc = TEST_FAILED
            finally:
                test.update_overall_rc()
                cert_prints.stop_test_logs(test)
        if test.rc == TEST_FAILED:
            failures += 1
            if "connection_test" in test.module_name and f"{EXIT_CERT}" in test.get_phase_reason(TEST_BODY):
                exit_on_test_failure = True
        cert_prints.wlt_print(f"Test Duration: {test.duration}")
        cert_prints.wlt_print(tabulate.tabulate([[i+1, i+1-(failures+skipped), skipped, failures, len(tests)]],
                            headers=["FINISHED", "PASSED", "SKIPPED", "FAILED", "TOTAL"], tablefmt="pretty"))
        if test.rc != TEST_SKIPPED:
            cert_prints.wait_time_n_print(2)
        if exit_on_test_failure and test.rc == TEST_FAILED:
            break

    # Print results
    cert_results.generate_results_files(html=True, pdf=True, failures=failures, skipped=skipped, start_time=start_time, tests=tests, non_cert_run=args.non_cert_run)
    if not cert_prints.pipeline_running():
        webbrowser.open('file://' + os.path.realpath(os.path.join(ARTIFACTS_DIR, UT_RESULT_FILE_PDF)))

    if failures:
        sys.exit(-1)

if __name__ == '__main__':
    main()
