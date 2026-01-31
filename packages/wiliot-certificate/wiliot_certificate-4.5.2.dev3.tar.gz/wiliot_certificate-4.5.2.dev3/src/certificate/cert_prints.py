from certificate.cert_defines import *
import time, datetime
import sys
import json
import os
import re
import logging
import logging.handlers

COLORS = {
    "HEADER" : '\033[95m',
    "BLUE" : '\033[94m',
    "CYAN" : '\033[96m',
    "GREEN" : '\033[92m',
    "WARNING" : '\033[93m',
    "RED" : '\033[91m',
    "ENDC" : '\033[0m',
    "BOLD" : '\033[1m',
    "UNDERLINE" : '\033[4m',
}
color = lambda c, t : COLORS["BOLD"]+COLORS[c]+t+COLORS["ENDC"]
pipeline_running = lambda : True if 'BITBUCKET_BUILD_NUMBER' in os.environ else False
camelcase_to_title = lambda s: ' '.join(word.capitalize() for word in re.split('(?=[A-Z])', s))
SEP = '\n' + '#'*100 + '\n'
SEP2 = '\n' + '#'*100 + '\n' + '#'*100 + '\n'
WIL_CERT_TEXT = r'''
 __        _____ _     ___ ___ _____    ____ _____ ____ _____ ___ _____ ___ ____    _  _____ _____ 
 \ \      / /_ _| |   |_ _/ _ \_   _|  / ___| ____|  _ \_   _|_ _|  ___|_ _/ ___|  / \|_   _| ____|
  \ \ /\ / / | || |    | | | | || |   | |   |  _| | |_) || |  | || |_   | | |     / _ \ | | |  _|  
   \ V  V /  | || |___ | | |_| || |   | |___| |___|  _ < | |  | ||  _|  | | |___ / ___ \| | | |___ 
    \_/\_/  |___|_____|___\___/ |_|    \____|_____|_| \_\|_| |___|_|   |___\____/_/   \_\_| |_____|
                                                                                                   
'''

hex_str2int = lambda s : int(s, 16)

# Logger defines
NOTSET   = logging.NOTSET    # 0
DEBUG    = logging.DEBUG     # 10
INFO     = logging.INFO      # 20
WARNING  = logging.WARNING   # 30
ERROR    = logging.ERROR     # 40
CRITICAL = logging.CRITICAL  # 50
CONSOLE_FILTER = "to_console"
TEXT_FILTER = "to_text"
MQTT_FILTER = "to_mqtt"
TEST_MAQTT_FILTER = "mqtt_topic"
TEST_MQTT_CLIENT = "mqtt_client"
COLOR_ATTR = "color_name"
CERT_LOGGER = "certificate"
_logger = None

# Logger functions #
####################

def create_filter(flag_name):
    class _FlagFilter(logging.Filter):
        def filter(self, record):
            return getattr(record, flag_name, False)
    return _FlagFilter()

def has_active_test_handlers():
    logger = logging.getLogger(CERT_LOGGER)
    return any(getattr(handler, "is_test_handler", False) for handler in logger.handlers)

class TestDebugFilter(logging.Filter):
    def filter(self, record):
        return has_active_test_handlers() and getattr(record, TEXT_FILTER, False)

class TestMqttAllFilter(logging.Filter):
    def __init__(self, client_key):
        super().__init__()
        self.client_key = client_key

    def filter(self, record):
        target_client = getattr(record, TEST_MQTT_CLIENT, None)
        return (
            getattr(record, MQTT_FILTER, False)
            and has_active_test_handlers()
            and (target_client == self.client_key or target_client == BOTH)
        )

class TestMqttTopicFilter(logging.Filter):
    def __init__(self, topic_key, client_key):
        super().__init__()
        self.topic_key = topic_key  # "data" / "status" / "update"
        self.client_key = client_key

    def filter(self, record):
        target_client = getattr(record, TEST_MQTT_CLIENT, None)
        mqtt_topic = getattr(record, TEST_MAQTT_FILTER, "")
        return (
            has_active_test_handlers()
            and getattr(record, MQTT_FILTER, False)
            and (target_client == self.client_key or target_client == BOTH)
            and (self.topic_key in mqtt_topic or mqtt_topic == ALL_TOPICS)
        )

class ColorFormatter(logging.Formatter):
    def format(self, record):
        msg = super().format(record)
        color_name = getattr(record, COLOR_ATTR, "")
        if color_name and color_name in COLORS:
            return color(color_name, msg)
        return msg


def init_logging(log_level=INFO, mqtt_level=INFO):
    os.makedirs(ARTIFACTS_DIR, exist_ok=True)
    global _logger
    if _logger:
        return _logger

    logger = logging.getLogger(CERT_LOGGER)
    # To allow all prints pass and leave the filtering to the .log command
    logger.setLevel(DEBUG)

    # Console handler
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(log_level)
    console.addFilter(create_filter(CONSOLE_FILTER))
    console.setFormatter(ColorFormatter("%(message)s"))
    logger.addHandler(console)

    # Main text file handler
    text_path = os.path.join(ARTIFACTS_DIR, DATA_SIM_LOG_FILE)
    text_h = logging.FileHandler(text_path, mode="a", encoding="utf-8")
    text_h.setLevel(log_level)
    text_h.addFilter(create_filter(TEXT_FILTER))
    text_h.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(text_h)

    # Main MQTT file handler
    mqtt_path = os.path.join(ARTIFACTS_DIR, CERT_MQTT_LOG_FILE)
    mqtt_h = logging.FileHandler(mqtt_path, mode="a", encoding="utf-8")
    mqtt_h.setLevel(mqtt_level)
    mqtt_h.addFilter(create_filter(MQTT_FILTER))
    mqtt_h.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(mqtt_h)

    _logger = logger
    return logger


def start_test_logs(test, dut_mqtt_exist):
    os.makedirs(os.path.join(ARTIFACTS_DIR,test.dir), exist_ok=True)
    logger = logging.getLogger(CERT_LOGGER)
    debug_path = os.path.join(ARTIFACTS_DIR, test.dir, f"{test.module_name}_debug.log")
    debug_log = logging.FileHandler(debug_path, mode="w", encoding="utf-8")
    debug_log.setLevel(DEBUG)
    debug_log.addFilter(TestDebugFilter())
    debug_log.setFormatter(logging.Formatter("%(message)s"))
    debug_log.is_test_handler = True
    logger.addHandler(debug_log)

    handlers = {}
    client_keys = [DUT, TESTER]
    for client_key in client_keys:
        client_handlers = {}
        all_path = os.path.join(ARTIFACTS_DIR, test.dir, f"{MQTT_LOG_PRE_STR}{client_key}_all.json")
        mqtt_all_hand = logging.FileHandler(all_path, mode="w", encoding="utf-8")
        mqtt_all_hand.setLevel(INFO)
        mqtt_all_hand.addFilter(TestMqttAllFilter(client_key))
        mqtt_all_hand.setFormatter(logging.Formatter("%(message)s"))
        mqtt_all_hand.is_test_handler = True
        logger.addHandler(mqtt_all_hand)
        client_handlers[ALL] = mqtt_all_hand

        for topic in (DATA, STATUS, UPDATE):
            path = os.path.join(ARTIFACTS_DIR, test.dir, f"{MQTT_LOG_PRE_STR}{client_key}_{topic}.json")
            handler = logging.FileHandler(path, mode="w", encoding="utf-8")
            handler.setLevel(INFO)
            handler.addFilter(TestMqttTopicFilter(topic, client_key))
            handler.setFormatter(logging.Formatter("%(message)s"))
            handler.is_test_handler = True
            logger.addHandler(handler)
            client_handlers[topic] = handler
        handlers[client_key] = client_handlers

    test.debug_path = debug_path
    test.debug_log = debug_log
    test.mqtt_handlers = handlers

    return test


def stop_test_logs(test):
    logger = logging.getLogger(CERT_LOGGER)
    logger.removeHandler(test.debug_log)
    test.debug_log.close()
    for client_handlers in test.mqtt_handlers.values():
        for handler in client_handlers.values():
            logger.removeHandler(handler)
            handler.close()


# Printing functions #
######################

# Allows to print to all ouptus according to the filters
def wlt_print(text, chosen_color="", log_level=INFO, to_console=True, to_text=True, to_mqtt=False, mqtt_topic=None, target=DUT):
    logger = logging.getLogger(CERT_LOGGER)
    logger.log(
        log_level,
        text,
        extra={
            CONSOLE_FILTER: to_console,
            TEXT_FILTER: to_text,
            MQTT_FILTER: to_mqtt,
            TEST_MAQTT_FILTER: (mqtt_topic or "").lower(),
            TEST_MQTT_CLIENT: target,
            COLOR_ATTR: chosen_color.upper() if chosen_color else "",
        },
    )


def print_pass_or_fail(rc, text):
    if rc:
        wlt_print(text+" PASSED!", "GREEN")
    else:
        wlt_print(text+" FAILED!", "RED")


def phase_run_print(func):
    txt = f"{SEP2}==>> Phase {func}{SEP2}\n"
    wlt_print(txt, "CYAN", to_mqtt=True, mqtt_topic=ALL_TOPICS, target=BOTH)


def functionality_run_print(func):
    txt = f"{SEP}==>> Running {func}\n"
    wlt_print(txt, "HEADER", to_mqtt=True, mqtt_topic=ALL_TOPICS, target=BOTH)


def test_epilog_print(test):
    if any([phase.rc == TEST_FAILED for phase in test.phases]):
        wlt_print(test.reason, "RED")
        wlt_print("==>> Test {} failed!\n".format(test.module_name), "RED")
    else:
        wlt_print(test.reason, "GREEN")
        wlt_print("==>> Test {} passed!\n".format(test.module_name), "GREEN")


def test_json_print(test):
    for key, value in test.test_json.items():
        if key == 'procedure':
            wlt_print(f"    {camelcase_to_title(key)}:")
            for i in range(len(value)):
                wlt_print(f"        ({i}) {value[i]}")
        else:
            wlt_print(f"    {camelcase_to_title(key)}: {value}")


def test_run_print(test):
    brg_txt = ""
    if test.params:
        params = " (params: {})".format(test.params)
    else:
        params = " (without params)"
    if test.active_brg:
        brg_txt = " ({}: {}".format("INTERNAL BRG" if test.internal_brg else "BRG", test.active_brg.id_str)
        if test.brg1 and test.multi_brg:
            brg_txt += " & " + test.brg1.id_str
        brg_txt += ")"
    functionality_run_print(f"{test.module_name}{params}{brg_txt}{SEP}")
    wlt_print("Test Information:\n", "HEADER")
    test_json_print(test)
    wlt_print("Test Configuration:", "HEADER")
    params = [{'name':p.name, 'value':p.value} for p in test.params]
    wlt_print(f"""    - internal_brg={test.internal_brg}\n    - tester={test.tester}
    - dut={test.dut}\n    - brg1={test.brg1}\n    - active_brg={test.active_brg}
    - params={params}\n""")


def field_functionality_pass_fail_print(test, field, value=""):
    print_string = f"{field}={value}"
    if value == "":
        print_string = str(field)
    if test.rc == TEST_FAILED:
        wlt_print(print_string + " functionality failed!\n", "RED")
        wlt_print(test.reason, "RED")
    elif test.rc == TEST_SKIPPED:
        wlt_print(print_string + " functionality skipped!\n", "WARNING")
    else:
        wlt_print(print_string + " functionality passed!\n", "GREEN")


def print_update_wait(secs=1):
    sys.stdout.write(".")
    sys.stdout.flush()
    time.sleep(secs)


def wait_time_n_print(secs, txt=""):
    if txt:
        wlt_print(txt, "CYAN")
    wlt_print(f"Waiting for {secs} seconds", "CYAN")
    while secs:
        print_update_wait()
        secs -= 1
    wlt_print("\n")


def mqtt_scan_wait(test, duration, target=DUT):
    mqttc = test.get_mqttc_by_target(target)
    gw = test.dut if target == DUT else test.tester
    wlt_print("Scanning mqtt packets on {} for {} seconds...".format(gw.id_str, duration), "WARNING")
    sys.stdout.flush()
    chars = ["|", "/", "-", "\\"]
    start_time = datetime.datetime.now()
    i = 0
    while True:
        cur_duration = (datetime.datetime.now() - start_time).seconds
        if cur_duration >= duration:
            break
        if pipeline_running():
            sys.stdout.write(".")
        else:
            sys.stdout.write("\r"+chars[i%4]*20+" "+str(cur_duration)+" "+chars[i%4]*20+" {} pkts captured".format(len(mqttc._userdata[PKTS].data)))
        sys.stdout.flush()
        time.sleep(0.25)
        i += 1
    wlt_print("\n")


def print_pkt(p):
    wlt_print(datetime.datetime.now().strftime("%d/%m/%Y, %H:%M:%S"))
    wlt_print(json.dumps(p, indent=4, default=lambda o: o.__dict__, sort_keys=True))


def generate_print_string(fields_and_values):
    list_to_print = []
    for f in fields_and_values:
        list_to_print.append(str(f) + "=" + str(fields_and_values[f]))
    return " & ".join(list_to_print)
