from certificate.cert_prints import *
from certificate.cert_defines import *
from certificate.wlt_types import *
import certificate.cert_common as cert_common
import certificate.cert_config as cert_config


def action_restore_defaults_test_epilog(test, revert_brgs=True):
    # Test result print
    field_functionality_pass_fail_print(test, "action_restore_defaults")
    return cert_common.test_epilog(test, revert_brgs=revert_brgs)


def run(test):
    test = cert_common.test_prolog(test)
    if test.rc == TEST_FAILED:
        return cert_common.test_epilog(test)

    functionality_run_print("action_restore_defaults")

    # non-default cfg
    test = cert_common.brg_non_default_modules_cfg(test)
    if test.rc == TEST_FAILED and test.exit_on_param_failure:
        return action_restore_defaults_test_epilog(test, revert_brgs=True)
    # sample non-default cfg_hash
    test, non_default_hash = cert_common.get_cfg_hash(test)
    if test.rc == TEST_FAILED:
        return action_restore_defaults_test_epilog(test, revert_brgs=True)
    # send action
    cert_config.send_brg_action(test, ag.ACTION_RESTORE_DEFAULTS)
    # analysis
    expected_hash = test.active_brg.cfg_hash
    wlt_print("Analyzing Restore Defaults", "BLUE")
    # First 30 for wlt app start + 10 sec extra for brg to settle to recieve its get module action
    wait_time_n_print(40, txt="Analyzing Restore Defaults")

    cfg_once = True
    test.get_mqttc_by_target(DUT).flush_pkts()

    wlt_print(f"Get Interface Module from BRG {test.active_brg.id_str}")
    test, if_pkt = cert_common.get_module_if_pkt(test)
    if test.rc == TEST_FAILED:
        return action_restore_defaults_test_epilog(test, revert_brgs=True)

    received_hash = if_pkt.cfg_hash
    wlt_print(
        f"\nExpected cfg_hash: 0x{expected_hash:08X}\n"
        f"Received cfg_hash: 0x{received_hash:08X}\n"
        f"Non default cfg_hash: 0x{non_default_hash:08X}"
    )
    if received_hash == non_default_hash:
        test.rc = TEST_FAILED
        test.add_reason("received_hash is equal to non_default_hash, ACTION_RESTORE_DEFAULTS was not received by the brg!")
        return action_restore_defaults_test_epilog(test, revert_brgs=True)
    elif received_hash == expected_hash:
        return action_restore_defaults_test_epilog(test)
    else:
        # Default SUB1G EP in the BRG is 0 and in the UT (in case of data=tags) it's 9.
        # In order to align BRG cfg to the suitable default cfg,
        # we should configure sub1g ep individually once after reboot when cfg hash was changed but still doesn't match.
        if ag.MODULE_ENERGY_SUB1G in test.active_brg.sup_caps and cfg_once:
            cfg_once = False
            cfg_pkt = cert_config.get_default_brg_pkt(test,
                                                      test.active_brg.energy_sub1g,
                                                      **{BRG_PATTERN: ag.SUB1G_ENERGY_PATTERN_ISRAEL})
            test = cert_config.brg_configure(test, cfg_pkt=cfg_pkt)[0]
            if test.rc == TEST_FAILED:
                return action_restore_defaults_test_epilog(test, revert_brgs=True)

    return action_restore_defaults_test_epilog(test)
