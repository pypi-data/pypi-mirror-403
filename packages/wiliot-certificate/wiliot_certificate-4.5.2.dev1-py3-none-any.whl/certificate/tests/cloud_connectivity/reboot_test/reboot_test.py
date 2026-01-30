import datetime

from certificate.cert_prints import *
from certificate.cert_defines import *
from certificate.wlt_types import *
import certificate.cert_common as cert_common
import certificate.cert_config as cert_config
from common.api_if.api_validation import api_validation


# DEFINES
TIMEOUT_IN_MINUTES = 3


def run(test):
    test = cert_common.test_prolog(test)
    if test.rc == TEST_FAILED:
        return cert_common.test_epilog(test)

    # Stage setup
    phase_run_print("Reboot started")

    # Initiate action
    dut_mqttc = test.get_mqttc_by_target(DUT)
    wlt_print(f"Publishing reboot action to {dut_mqttc.update_topic}. Awaiting reboot.. (timeout is {TIMEOUT_IN_MINUTES} minutes)")
    cert_config.gw_action(test, f"{REBOOT_GW_ACTION}", target=DUT)
    dut_mqttc.flush_pkts()

    # Wait for response
    gw_type = None
    wlt_print(f'Waiting for GW to connect... (Timeout {TIMEOUT_IN_MINUTES} minutes)')
    timeout = datetime.datetime.now() + datetime.timedelta(minutes=TIMEOUT_IN_MINUTES)
    while datetime.datetime.now() < timeout:
        gw_type, msg = cert_common.get_gw_type(dut_mqttc)
        if gw_type is not None:
            break
        print_update_wait(5)

    # Analyze results
    if gw_type is None:
        test.rc = TEST_FAILED
        test.reason = "The gateway did not reboot properly, status message was not received"
    elif gw_type == "other":
        test.rc = TEST_FAILED
        test.reason = f"gatewayType must be defined in the status message {msg}"
    else:
        wlt_print("Gateway rebooted and uploaded a configuration message as expected.", "GREEN")
        wlt_print(f"The configuration message received:\n {msg}")

    wlt_print("Checking the status message matches API format...")
    test = api_validation(test)

    return cert_common.test_epilog(test)
