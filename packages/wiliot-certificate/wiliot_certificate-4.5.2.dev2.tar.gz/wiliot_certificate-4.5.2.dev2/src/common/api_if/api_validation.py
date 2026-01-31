import json
from jsonschema import Draft202012Validator
from importlib import resources
from enum import Enum

from certificate.cert_prints import *
from certificate.cert_defines import GW_LOGS
import certificate.cert_utils as cert_utils
import certificate.cert_mqtt as cert_mqtt


API_VALIDATION = "API Validation"
BLE_ADDRESS = "bleAddress"
REPORT_FILE = 'api_validation_report.txt'


class MESSAGE_TYPES(Enum):
    STATUS = "status"
    DATA = "data"
    LOGS = "logs"


def validate_received_packets(pkts_array):
    for pkt in pkts_array:
        # Check all required fields are present
        if TIMESTAMP not in pkt:
            return False, "timestamp field is missing in some of the packets"
        if ALIAS_BRIDGE_ID not in pkt:
            return False, "alias_bridge_id field is missing in some of the packets"
        if PAYLOAD not in pkt:
            return False, "payload field is missing in some of the packets"
        if SEQUENCE_ID not in pkt:
            return False, "sequence_id field is missing in some of the packets"
        # Check that the payload length is either 62 or 74 hex characters (equevelnt to 31 or 37 bytes)
        if len(pkt[PAYLOAD]) != 62 and len(pkt[PAYLOAD]) !=74:
            return False, f"Payload length is invalid for packet {pkt[PAYLOAD]}"
    return True, ""

def get_gw_status_msg_pb(mqttc):
    messages = cert_mqtt.get_all_status_pkts(mqttc)
    for msg in messages:
        if GW_STATUS in msg: # protobuf
            return msg[GW_STATUS]
    return None

def validate_status_message_pb(status_msg):
    '''
    When a protobuf field is set to default value, it is not encoded before sending.
    This function validates the mandatory fields where the default value is unacceptable.
    '''
    status_msg = status_msg.get(GW_STATUS)
    if status_msg == None:
        return False, [f"Missing {GW_STATUS} uplink msg"]

    mandatory_fields = [GW_ID, GW_TYPE, GW_API_VERSION, BLE_ADDRESS]
    missing_fields = []

    for field in mandatory_fields:
        if field not in status_msg.keys() or not status_msg[field]:
            missing_fields.append(field)
    if missing_fields:
        return False, [f"Missing {missing_fields} in status msg"]
    
    # GWs must report either version, or ble + interface versions
    version_field = {VERSION: False, WIFI_VERSION_PB: False, BLE_VERSION_PB: False}
    for key in status_msg.keys():
        if key in version_field.keys():
            version_field[key] = True
    if not version_field[VERSION] and not all((version_field[BLE_VERSION_PB], version_field[WIFI_VERSION_PB])):
        return False, [f"Missing {VERSION} in status msg"]

    return True, [""]

def api_validation(test, msg_type=MESSAGE_TYPES.STATUS, msgs=[]):
    phase_run_print(API_VALIDATION)
    api_validation_phase = cert_utils.Phase(API_VALIDATION, rc=TEST_PASSED)

    if not test.dut.gw_api_version:
        wlt_print("API validation is skipped because no API version was specified", "WARNING")
        api_validation_phase.rc = TEST_FAILED
        api_validation_phase.reason = "API validation is skipped because no API version was specified"
        test.add_phase(api_validation_phase)
        return test
    elif test.dut.protobuf:
        def validate_message(message: dict, msg_type=MESSAGE_TYPES.DATA.value) -> tuple[bool, str]:
            if msg_type == MESSAGE_TYPES.STATUS.value:
                return validate_status_message_pb(message)
            elif msg_type == MESSAGE_TYPES.LOGS.value:
                # No validation for gw logs
                return True, [""]
            else:
                pkts_array = [pkt for pkt in message.get(PACKETS, {})]
                valid, error = validate_received_packets(pkts_array)
                return valid, [error]
    else:
        def validate_message(message: dict, msg_type=MESSAGE_TYPES.DATA.value) -> tuple[bool, str]:
            json_path = resources.files(__package__) / f"{test.dut.gw_api_version}/{msg_type}.json"
            with json_path.open() as f:
                relevant_schema = json.load(f)
            validator = Draft202012Validator(relevant_schema)
            valid = validator.is_valid(message)
            errors = [e.message for e in validator.iter_errors(message)]
            return (valid, errors)

    wlt_print(f"Validating {msg_type.value} messages in the test according to API version {test.dut.gw_api_version} validation schema", "BLUE")
    report = []
    # If function wasn't given the msgs to verify, get them from mqtt
    if not msgs:
        if msg_type.value == MESSAGE_TYPES.STATUS.value:
            msgs = [msg.body for msg in test.get_mqttc_by_target(DUT)._userdata[PKTS].status if GW_LOGS not in msg.body]
        elif msg_type.value == MESSAGE_TYPES.LOGS.value:
            msgs = [msg.body for msg in test.get_mqttc_by_target(DUT)._userdata[PKTS].status if GW_LOGS in msg.body]
        else:
            msgs = [msg.body for msg in test.get_mqttc_by_target(DUT)._userdata[PKTS].data]

    error_report = []
    validation = (True, [])
    for idx, message_body in enumerate(msgs):
        if msg_type.value == MESSAGE_TYPES.DATA.value and len(message_body[PACKETS]) == 0:
            continue
        validation = validate_message(message_body, msg_type.value)
        errors = []
        if not validation[0]:
            api_validation_phase.rc = TEST_FAILED
            api_validation_phase.reason = f"API is invalid, details in {REPORT_FILE}"
            for e in validation[1]:
                if e not in errors:
                    errors.append(e)
            error_report.append(f'The errors in message (idx={idx}, json timestamp={message_body.get(TIMESTAMP)}) Errors:')
            for idx, e in enumerate(errors):
                error_report.append(f'Error number {idx}:\n {e}')
    report.append("\n")
    report.append(f'Summary for {msg_type.value} messages')
    report.append(f'valid: {validation[0]}, num of errors: {len(errors)}')
    report.append('******************************************************\n')
    report.extend(error_report)
    wlt_print("\nAPI validation errors:", "BLUE")
    for line in report:
        wlt_print(line)
    report_path = os.path.join(ARTIFACTS_DIR, test.dir, REPORT_FILE)
    with open(report_path, 'w') as f:
        for line in report:
            f.write(str(line) + '\n')
    field_functionality_pass_fail_print(api_validation_phase, API_VALIDATION)
    test.add_phase(api_validation_phase)
    return test