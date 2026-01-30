import datetime

from certificate import cert_config
from certificate.cert_prints import *
from certificate.cert_defines import *
from certificate.wlt_types import *
import certificate.cert_common as cert_common
from common.api_if.api_validation import api_validation

# DEFINES
TIMEOUT_IN_MINUTES = 3


def run(test):
    test = cert_common.test_prolog(test)
    if test.rc == TEST_FAILED:
        return cert_common.test_epilog(test)

    # Stage setup
    phase_run_print("Connection test started")
    dut_mqttc = test.get_mqttc_by_target(DUT)

    # Initiate action
    if not pipeline_running() and not test.ci_cd:
        warning_prefix = COLORS["WARNING"]
        warning_suffix = COLORS["ENDC"]
        dut_mqttc.flush_pkts()
        input((f'{warning_prefix}TESTING CONNECTION RECOVERY AFTER POWER CYCLE OF THE GATEWAY\n'
               "Please unplug and then plug GW back into power. Press enter when finished"
               f"{warning_suffix}"))
    else:
        # If this test runs as part of a pipeline, act like the reboot test and don't demand a manual disconnect & connect
        wlt_print(f"Publishing reboot action to {dut_mqttc.update_topic}. Awaiting reconnect.. (timeout is {TIMEOUT_IN_MINUTES} minutes)")
        dut_mqttc.flush_pkts()
        cert_config.gw_action(test, f"{REBOOT_GW_ACTION}", target=DUT)

    # Wait for response
    gw_type = None
    gw_api_version = None
    wlt_print(f'Waiting for GW to connect... (Timeout {TIMEOUT_IN_MINUTES} minutes)')
    timeout = datetime.datetime.now() + datetime.timedelta(minutes=TIMEOUT_IN_MINUTES)
    while datetime.datetime.now() < timeout:
        gw_type, msg = cert_common.get_gw_type(dut_mqttc)
        gw_api_version = cert_common.get_gw_api_version(dut_mqttc)
        if gw_type is not None:
            break
        print_update_wait(5)

    # Check GW API version VS user initial version input
    if gw_api_version is not None and int(test.dut.gw_api_version) != int(gw_api_version):
        wlt_print(
            f"User inserted the wrong GW API version. version inserted was {test.dut.gw_api_version}. "
            f"Actual version is {gw_api_version}."
        )
        wlt_print(
            f"{EXIT_CERT} Make sure you are running the correct API version",
            chosen_color="ERROR",
        )
        test.rc = TEST_FAILED
        test.reason = f"{EXIT_CERT} Make sure you are running the correct API version"
    elif gw_type is None:
        test.rc = TEST_FAILED
        test.reason = f"{EXIT_CERT} The gateway did not reboot properly, status message was not received"
    elif gw_type == "other":
        test.rc = TEST_FAILED
        test.reason = f"{EXIT_CERT} gatewayType must be defined in the status message {msg}"
    else:
        wlt_print("Gateway rebooted and uploaded a configuration message as expected.", "GREEN")
        wlt_print(f"The configuration message received:\n {msg}")

    if test.rc != TEST_FAILED:
        wlt_print("Checking the status message matches API format...")
        test = api_validation(test)

    return cert_common.test_epilog(test)
