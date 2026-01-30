
import os
import copy
import random
import shutil
import tabulate
import importlib # needed for importing all of the tests
from requests import codes as r_codes

# Local imports
import certificate.cert_config as cert_config
import certificate.cert_common as cert_common
import certificate.cert_results as cert_results
from certificate.wlt_types import *
from certificate.cert_defines import *
from certificate.cert_prints import *

MULTI_BRG_STR =     "multi_brg"  # used for multi brg tests
GW_ONLY_STR =       "gw_only"  # used for gw only tests
INTERNAL_BRG_STR =  "internal_brg"
ORIGINAL_AG_FILE =  "wlt_types_ag.py"

# Tester specific definitions
TESTER_FW_VERSIONS = ["4.6.26", "4.6.27"]
MAX_OUTPUT_POWER_PER_TESTER_BOARD_TYPE = {ag.BOARD_TYPE_FANSTEL_WIFI_V0: 8, ag.BOARD_TYPE_FANSTEL_LAN_V0: 8, ag.BOARD_TYPE_MINEW_POE_V0: 2}
DUAL_POLARIZATION_ANTENNA_PER_TESTER_BOARD_TYPE = {ag.BOARD_TYPE_FANSTEL_WIFI_V0: False, ag.BOARD_TYPE_FANSTEL_LAN_V0: False, ag.BOARD_TYPE_MINEW_POE_V0: True}

##################################
# Utils
##################################

module_name_id2py = lambda module_id: module_mapping(module_id, from_attr=MODULE_ID, to_attr=MODULE_PY_NAME)
module_name_py2id = lambda module_py_name: module_mapping(module_py_name, from_attr=MODULE_PY_NAME, to_attr=MODULE_ID)
module_name_cloud2py = lambda module_cloud_name: module_mapping(module_cloud_name, from_attr=MODULE_CLOUD_NAME, to_attr=MODULE_PY_NAME)
module_name_cloud2id = lambda module_cloud_name: module_mapping(module_cloud_name, from_attr=MODULE_CLOUD_NAME, to_attr=MODULE_ID)
module_name_py2cloud = lambda module_py_name: module_mapping(module_py_name, from_attr=MODULE_PY_NAME, to_attr=MODULE_CLOUD_NAME)
module_name_id2display = lambda module_id: module_mapping(module_id, from_attr=MODULE_ID, to_attr=MODULE_DISPLAY_NAME)

def module_mapping(input, from_attr=MODULE_ID, to_attr=MODULE_PY_NAME):
    for module in ag.MODULES_LIST:
        if getattr(module, from_attr, None) == input:
            return getattr(module, to_attr, None)
    return None

def load_module(module_name, module_path, rel_path="."):
    spec = importlib.util.spec_from_file_location(module_name, os.path.join(BASE_DIR, rel_path, module_path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def handle_error(error, start_time):
    wlt_print(error, "red")
    cert_results.generate_results_files(html=True, pdf=False, start_time=start_time, error=error)
    sys.exit(-1)

def overwrite_defines_file(file_name, brg_id, overwrite_defs):
    overwritten = {key: False for key in overwrite_defs}
    with open(os.path.join(BASE_DIR, "ag", file_name), "r") as f:
        lines = f.readlines()
    for i, line in enumerate(lines):
        for key,val in overwrite_defs.items():
            pattern = r"^(\s*" + re.escape(key) + r"\s*=\s*).*$" # match the key before the "=", capture it, then replace what's after
            if re.match(pattern, line):
                lines[i] = re.sub(pattern, rf"\g<1>{val}", line)
                overwritten[key] = True
                break
    for key,flag in overwritten.items():
        if not flag:
            wlt_print(f"Couldn't overwrite '{key}' as it was not found in {file_name}!", "WARNING")
    with open(os.path.join(BASE_DIR, "ag", file_name.replace('.py', f'_overwritten_for_{brg_id}.py')), "w") as f:
        f.writelines(lines)
    return file_name.replace('.py', f'_overwritten_for_{brg_id}.py')

def parse_cfg_file(filepath):
    config = {}
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue  # skip empty lines and comments
            if "=" in line:
                key, value = line.split("=", 1)
                config[key.strip()] = value.strip()
    return config

##################################
# Schema Validation
##################################

def format_unrecognized_schema_errors(unrecognized_modules, module_errors, device_str):
    """Format unrecognized schema items into a concise error message."""
    parts = [f"<strong>Unrecognized items in {device_str} validation schema:</strong>"]
    
    # Unrecognized modules
    if unrecognized_modules:
        parts.append(f"  <strong>Unrecognized modules:</strong> [{', '.join(unrecognized_modules)}]")
    
    # Separate unrecognized fields, attributes, and enum values
    unrecognized_fields_by_module = {}
    unrecognized_attributes_by_module = {}
    unrecognized_enum_values_by_module = {}
    
    for module, fields in module_errors.items():
        for field, errors in fields.items():
            if errors["unrecognized_field"]:
                if module not in unrecognized_fields_by_module:
                    unrecognized_fields_by_module[module] = []
                unrecognized_fields_by_module[module].append(field)
            if errors["attributes"]:
                if module not in unrecognized_attributes_by_module:
                    unrecognized_attributes_by_module[module] = {}
                unrecognized_attributes_by_module[module][field] = errors["attributes"]
            if errors["enum_values"]:
                if module not in unrecognized_enum_values_by_module:
                    unrecognized_enum_values_by_module[module] = {}
                unrecognized_enum_values_by_module[module][field] = errors["enum_values"]
    
    # Unrecognized fields
    if unrecognized_fields_by_module:
        parts.append("  <strong>Unrecognized fields:</strong>")
        for module, fields in unrecognized_fields_by_module.items():
            parts.append(f"    {module}: [{', '.join(fields)}]")
    
    # Unrecognized attributes
    if unrecognized_attributes_by_module:
        parts.append("  <strong>Unrecognized attributes:</strong>")
        for module, fields in unrecognized_attributes_by_module.items():
            for field, attrs in fields.items():
                parts.append(f"    {module}: {field}: [{', '.join(attrs)}]")
    
    # Unrecognized enum values
    if unrecognized_enum_values_by_module:
        parts.append("  <strong>Unrecognized enum values:</strong>")
        for module, fields in unrecognized_enum_values_by_module.items():
            for field, enum_vals in fields.items():
                parts.append(f"    {module}: {field}: [{', '.join(str(val) for val in enum_vals)}]")
    
    return "\n".join(parts)

def load_and_validate_schema(validation_schema_path, start_time=None, tester=False, gui=False, api_version=None):
    """Validate the uploaded schema file."""
    # Load the schema file
    device_str = ("tester's" if tester else "device under test's") if not gui else "given"
    error = ""
    try:
        with open(validation_schema_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not gui:
            wlt_print(f"The {device_str} validation schema is a valid JSON file", 'BLUE')
        os.makedirs(ARTIFACTS_DIR, exist_ok=True)
        shutil.copy2(validation_schema_path, os.path.join(ARTIFACTS_DIR, 'validation_schema.json'))
    except json.JSONDecodeError as e:
        error = f"The {device_str} validation schema is an invalid JSON file: {e}"
    except FileNotFoundError:
        error = f"The {device_str} validation schema file was not found!"
    except Exception as e:
        error = f"Unexpected error received trying to decode the {device_str} validation schema JSON file: {e}"
    if error:
        if gui:
            return False, error
        else:
            handle_error(error, start_time)

    # Basic validation: check for cloud_connectivity_flag or brg_flag
    if not (cloud_connectivity_flag(data) or brg_flag(data)):
        error = f"The {device_str} validation schema must support either cloud connectivity ('properties' field) or bridge device ('modules' field). None found."
        if gui:
            return False, error
        else:
            handle_error(error, start_time)
    
    # Check for missing defaults in all fields
    missing_defaults = []
    # Check top-level properties (gateway properties)
    if cloud_connectivity_flag(data) and isinstance(data["properties"], dict):
        missing_defaults.extend(check_missing_defaults_in_schema_properties(data["properties"], ""))
    # Check module properties (bridge modules)
    if brg_flag(data) and isinstance(data["modules"], dict):
        for module_name, module_def in data["modules"].items():
            if isinstance(module_def, dict) and "properties" in module_def:
                module_missing = check_missing_defaults_in_schema_properties(module_def["properties"], f"modules.{module_name}")
                missing_defaults.extend(module_missing)
    if missing_defaults:
        error = f"The following fields in the {device_str} validation schema are missing 'default' values:\n{'\n'.join(missing_defaults)}"
        if gui:
            return False, error
        else:
            handle_error(error, start_time)

    # Validate modules fields and values in the schema if brg_flag is True
    if brg_flag(data):
        # Use provided api_version parameter if available, otherwise use latest
        api_version = api_version if api_version else ag.API_VERSION_LATEST
        modules_data = data["modules"]
        # Go over all modules in the validation schema
        unrecognized_modules = []
        # Structure: {module_name: {field_name: {attributes: [...], enum_values: [...]}}}
        module_errors = {}
        for module in modules_data:
            module_id = module_name_cloud2id(module)
            if not module_id:
                unrecognized_modules.append(module)
                continue
            module_class = eval_pkt(ag.MODULES_DICT[module_id] + str(api_version))
            # Go over all fields in the module's properties
            for field in modules_data[module]["properties"].keys():
                if field not in module_class.field_metadata.keys():
                    if module not in module_errors:
                        module_errors[module] = {}
                    if field not in module_errors[module]:
                        module_errors[module][field] = {"unrecognized_field": True, "attributes": [], "enum_values": []}
                    continue
                # Go over all attributes in the field
                for attribute in modules_data[module]["properties"][field].keys():
                    if attribute not in list(module_class.field_metadata[field].keys()) + ["access"]:
                        if module not in module_errors:
                            module_errors[module] = {}
                        if field not in module_errors[module]:
                            module_errors[module][field] = {"unrecognized_field": False, "attributes": [], "enum_values": []}
                        module_errors[module][field]["attributes"].append(attribute)
                        continue
                    if attribute == "enum" and hasattr(module_class, "field_supported_values") and field in module_class.field_supported_values:
                        schema_enum_set = set(modules_data[module]["properties"][field][attribute]) 
                        support_set = set(module_class.field_supported_values[field])
                        unrecognized_enum_values = schema_enum_set - support_set
                        if unrecognized_enum_values:
                            if module not in module_errors:
                                module_errors[module] = {}
                            if field not in module_errors[module]:
                                module_errors[module][field] = {"unrecognized_field": False, "attributes": [], "enum_values": []}
                            module_errors[module][field]["enum_values"].extend(list(unrecognized_enum_values))
        # Construct error string if there are any unrecognized items
        if unrecognized_modules or module_errors:
            error = format_unrecognized_schema_errors(unrecognized_modules, module_errors, device_str)
            if gui:
                return False, error
            else:
                handle_error(re.sub(r'<[^>]+>', '', error), start_time)

    # Return the schema's data if all validation passed
    if gui:
        return True, data
    else:
        return data

def check_missing_defaults_in_schema_properties(properties, path_prefix=""):
    """
    Recursively check if all properties have default values.
    Returns list of field paths missing defaults.
    Properties with nested 'properties' (object types) don't need defaults themselves,
    only their nested properties need defaults.
    Array types with 'items' field also don't need defaults.
    """
    missing_defaults = []
    
    if not isinstance(properties, dict):
        return missing_defaults
    
    for field_name, field_def in properties.items():
        if not isinstance(field_def, dict):
            continue
            
        current_path = f"{path_prefix}.{field_name}" if path_prefix else field_name
        
        # Check if this field has nested properties
        has_nested_properties = "properties" in field_def and isinstance(field_def["properties"], dict)
        
        # Check if this is an array type with items
        is_array_with_items = field_def.get("type") == "array" and "items" in field_def
        
        # Only check for default if this property doesn't have nested properties and isn't an array with items
        # (Objects with nested properties and arrays with items don't need defaults themselves)
        if not has_nested_properties and not is_array_with_items and "default" not in field_def:
            missing_defaults.append(current_path)
        
        # Recursively check nested properties if they exist
        if has_nested_properties:
            nested_missing = check_missing_defaults_in_schema_properties(field_def["properties"], current_path)
            missing_defaults.extend(nested_missing)
    
    return missing_defaults

##################################
# Test
##################################

class WltTest:
    """
    Wiliot Test class representing a single test case.
    
    This class encapsulates all information needed to run a certification test,
    including gateway information, bridge information, test parameters, and test results.
    
    Attributes:
        name: Test name from test list
        tester: Gateway object (or string ID for backward compatibility)
        dut: Device under test object (or string ID for backward compatibility)
        brg1: Secondary bridge object for multi-bridge tests (optional)
        active_brg: Currently active bridge being tested
        test_json: Test configuration from JSON file
        phases: List of test phases
        params: List of test parameters
        rc: Test result code (TEST_PASSED, TEST_FAILED, TEST_SKIPPED, etc.)
        reason: Reason for test result
        start_time: Test start time
        end_time: Test end time
        duration: Test duration
        exit_on_param_failure: Whether to exit on parameter failure
        latest: Whether to use latest version
        release_candidate: Whether to use release candidate version
        sterile_run: Whether to run in sterile run mode
        data: Test data
        rand: Random number
    """
    def __init__(self, line, tester, dut, brg1=None, exit_on_param_failure=False,
                 latest=False, release_candidate=False, sterile_run=False, data='', ci_cd=False,
                 send_hb_before_sim=False):
        if line:
            test_list_line = line.strip().split()
            self.name = test_list_line[0]
            self.test_module = ag.MODULE_EMPTY # Default test module
            # Determine test's module
            for s in self.name.split('/'):
                module_py_name = module_name_id2py(s)
                if module_py_name:
                    self.test_module = module_py_name
                    break
            line_params = test_list_line[1:]
            self.dir = os.path.join("tests", self.name)
            self.module_name = os.path.join(os.path.basename(self.name))
            self.file = os.path.join(self.dir, os.path.basename(self.name)+".py")
            # Load test json
            test_json_file = open(os.path.join(BASE_DIR, self.dir, os.path.basename(self.name)+".json"))
            self.test_json = json.load(test_json_file)
            self.gw_only = self.test_json[GW_ONLY_TEST]
            self.multi_brg = self.test_json[MULTI_BRG_TEST]
            self.internal_brg = INTERNAL_BRG_STR in line_params
            if INTERNAL_BRG_STR in line_params: line_params.remove(INTERNAL_BRG_STR)
            self.create_test_phases_and_params(line_params)
        else:
            self.test_json = {}
            self.internal_brg = False
            self.multi_brg = False
            self.phases = [Phase(PRE_CONFIG), Phase(TEST_BODY), Phase(RESTORE_CONFIG)]
            self.params = []

        self.tester = tester
        self.dut = dut
        self.ci_cd = ci_cd
        # Actual brg to cfg - can be dut, its internal_brg or None
        if isinstance(self.dut, Bridge):
            self.active_brg = self.dut
        elif isinstance(self.dut, Gateway) and self.dut.has_internal_brg():
            self.active_brg = self.dut.internal_brg
        else:
            self.active_brg = None
        self.brg1 = brg1 if brg1 else (self.tester.internal_brg if tester and tester.internal_brg else None)
        self.rc = TEST_PASSED
        self.reason = ""
        self.start_time = None
        self.end_time = None
        self.duration = None
        self.exit_on_param_failure = exit_on_param_failure
        self.rand = random.randrange(255)
        self.latest = latest
        self.release_candidate = release_candidate
        self.sterile_run = sterile_run
        self.data = data
        self.debug_buffer = None
        self.debug_log = None
        self.mqtt_handlers = None
        self.send_hb_before_sim = send_hb_before_sim

    def create_test_phases_and_params(self, line_params):
        self.params = []
        phases_source = []
        dynamic_parameters = "dynamic_parameters" in self.test_json[ALL_SUPPORTED_VALUES]
        if dynamic_parameters:
            self.test_json[ALL_SUPPORTED_VALUES].remove("dynamic_parameters")
        if len(self.test_json[ALL_SUPPORTED_VALUES]) > 0:
            if dynamic_parameters:
                if line_params:
                    phases_source = line_params
                elif len(self.test_json[ALL_SUPPORTED_VALUES]) > 0:
                    phases_source = self.test_json[ALL_SUPPORTED_VALUES]
                else:
                    error = f"ERROR: No dynamic parameters provided for test {self.name}! Check test list file and update the supported values!\n{[f.__dict__ for f in self.phases]}"
                    handle_error(error, datetime.datetime.now())
            else:
                phases_source = self.test_json[ALL_SUPPORTED_VALUES]
            self.phases = [Phase(PRE_CONFIG)] + [Phase(phase) for phase in phases_source] + [Phase(RESTORE_CONFIG)]
            for param_phase in self.phases:
                param = Param(param_phase.name)
                if (param.name in line_params or param.value in [eval_param(p) for p in line_params]):
                    self.params += [param]
                else:
                    param_phase.tested = False
                    param_phase.rc = TEST_SKIPPED
            if all([param_phase.rc == TEST_SKIPPED for param_phase in self.phases]):
                error = f"ERROR: All params skipped for test {self.name}! Check test list file and update the supported values!\n{[f.__dict__ for f in self.phases]}"
                handle_error(error, datetime.datetime.now())
        else:
            if line_params:
                error = f"ERROR: For {self.name} params exist in test_list but not in test_json!\nline_params:{line_params}"
                handle_error(error, datetime.datetime.now())
            self.phases = [Phase(PRE_CONFIG), Phase(TEST_BODY), Phase(RESTORE_CONFIG)]

    
    def get_mqttc_by_target(self, target=DUT):
        if target == DUT:
            return self.dut.mqttc if isinstance(self.dut, Gateway) else self.tester.mqttc
        return self.tester.mqttc

    # Flush all existing mqtt packets
    def flush_all_mqtt_packets(self):
        self.get_mqttc_by_target(TESTER).flush_pkts()
        self.get_mqttc_by_target(DUT).flush_pkts()

    # Phase rc
    def set_phase_rc(self, phase_name, rc):
        phase = self.get_phase_by_name(phase_name)
        phase.rc = rc

    def get_phase_rc(self, phase_name):
        phase = self.get_phase_by_name(phase_name)
        return phase.rc

    # Phase reason
    def add_phase_reason(self, phase_name, reason):
        phase = self.get_phase_by_name(phase_name)
        if phase.reason:
            phase.reason += "\n"
        if reason not in phase.reason:
            phase.reason += reason

    def get_phase_reason(self, phase_name):
        phase = self.get_phase_by_name(phase_name)
        return phase.reason

    # Test funcs
    def get_phase_by_name(self, phase_name):
        for phase in self.phases:
            if phase.name == phase_name:
                return phase
        return None

    def add_phase(self, phase):
        self.phases[-1:-1] = [phase]

    def update_overall_rc(self):
        if any([phase.rc == TEST_FAILED or phase.rc == TEST_ABORTED for phase in self.phases]):
            self.rc = TEST_FAILED
    
    def reset_result(self):
        self.rc = TEST_PASSED
        self.reason = ""

    def get_seq_id(self):
        self.rand = (self.rand + 1) % 256
        return self.rand

    # TODO - remove when test reason is re-designed
    def add_reason(self, reason):
        if self.reason:
            self.reason += "\n"
        if reason not in self.reason:
            self.reason += reason

    def internal_id_alias(self):
        return self.dut.internal_brg.id_alias if isinstance(self.dut, Gateway) and self.dut.has_internal_brg() else self.tester.internal_brg.id_alias
    
    def dut_is_gateway(self):
        return isinstance(self.dut, Gateway)
    
    def dut_is_bridge(self):
        return isinstance(self.dut, Bridge)
    
    def dut_is_combo(self):
        return hasattr(self.dut, 'internal_brg') and self.dut.has_internal_brg()

##################################
# Phases
##################################
class Phase:
    def __init__(self, input=None, tested=True, rc=TEST_ABORTED, reason=""):
        self.name = str(input)
        self.tested = tested
        self.rc = rc
        self.reason = reason
    
    def __repr__(self):
        return self.name

##################################
# Param
##################################
class Param:
    def __init__(self, input=None):
        self.name = str(input)
        self.value = eval_param(input)
    
    def __repr__(self):
        return self.name

##################################
# Bridge
##################################
brg_flag = lambda validation_schema: 'modules' in validation_schema

class Bridge:
    def __init__(self, id_str="", board_type=0, cfg_hash=0, api_version=ag.API_VERSION_LATEST, interface_pkt=None, max_output_power_dbm=None, dual_polarization_antenna=True, rel_path=".", validation_schema=None):
        """
        Initialize a Bridge object.
        
        Args:
            id_str: Bridge ID string (hex format)
            board_type: Board type identifier (default: 0)
            cfg_hash: Configuration hash value (default: 0)
            api_version: Bridge API version (default: ag.API_VERSION_LATEST)
            interface_pkt: Interface packet containing bridge information (optional)
            max_output_power_dbm: Maximum output power in dBm (default: None)
            dual_polarization_antenna: Whether the bridge has a dual polarization antenna (default: True)
            rel_path: Relative path for loading modules (default: ".")
            validation_schema: Validation schema dictionary
        """
        self.id_str = id_str
        self.id_int = hex_str2int(id_str)
        self.id_alias = cert_common.hex2alias_id_get(id_str)
        self.board_type = interface_pkt.board_type if interface_pkt else board_type
        self.version = f"{interface_pkt.major_ver}.{interface_pkt.minor_ver}.{interface_pkt.patch_ver}" if interface_pkt else ""
        self.bl_version = interface_pkt.bl_version if interface_pkt else ""
        self.cfg_hash = interface_pkt.cfg_hash if interface_pkt else cfg_hash
        self.api_version = interface_pkt.api_version if interface_pkt else api_version
        self.validation_schema = validation_schema
        self.module_classes = {}
        if self.validation_schema:
            # Go over all modules in the validation schema
            for module in self.validation_schema:
                module_id = module_name_cloud2id(module)
                base_module_class = eval_pkt(ag.MODULES_DICT[module_id] + str(self.api_version))
                # Creates a new class that subclasses the shared module class. This gives us a per‑bridge class without touching the shared one.
                module_class = type(base_module_class.__name__, (base_module_class,), {})
                if hasattr(module_class, "field_metadata"):
                    module_class.field_metadata = copy.deepcopy(module_class.field_metadata)
                if hasattr(module_class, "field_supported_values"):
                    module_class.field_supported_values = copy.deepcopy(module_class.field_supported_values)
                self.module_classes[module_id] = module_class
                # Go over all fields in the module's properties
                for field in self.validation_schema[module]["properties"].keys():
                    if field not in module_class.field_metadata:
                        error = f"ERROR: Unrecognized field '{field}' in module '{module}'!"
                        handle_error(error, datetime.datetime.now())
                    # Go over all attributes in the field
                    for attribute in self.validation_schema[module]["properties"][field].keys():
                        if attribute not in module_class.field_metadata[field]:
                            if attribute == "access": continue  # skip access attribute
                            error = f"ERROR: Unrecognized attribute '{attribute}' in field '{field}' of module '{module}'!"
                            handle_error(error, datetime.datetime.now())
                        elif attribute == "enum":
                            if hasattr(module_class, "field_supported_values") and field in module_class.field_supported_values:
                                support = module_class.field_supported_values[field]
                                module_class.field_metadata[field][attribute] = [val for val in self.validation_schema[module]["properties"][field][attribute] if val in support]
                            else:
                                error = f"ERROR: Field '{field}' in module '{module}' is not recognized as an enum field!"
                                handle_error(error, datetime.datetime.now())
                        else:
                            module_class.field_metadata[field][attribute] = self.validation_schema[module]["properties"][field][attribute]
        self.max_output_power_dbm = max_output_power_dbm
        self.dual_polarization_antenna = dual_polarization_antenna
        self.sup_caps = []
        self.modules = []
        if interface_pkt:
            for key, value in interface_pkt.__dict__.items():
                if 'sup_cap_' in key and value:
                    module = key.replace('sup_cap_','')
                    module_id = module_name_py2id(module)
                    if module_id:
                        self.sup_caps += [module_id]
                        module_class = self.module_classes.get(module_id) or eval_pkt(ag.MODULES_DICT[module_id] + str(self.api_version))
                        self.modules += [module_class]
                        setattr(self, module, module_class)

    def update_modules(self):
        self.modules = []
        for sup_cap in self.sup_caps:
            module_class = self.module_classes.get(sup_cap) or eval_pkt(ag.MODULES_DICT[sup_cap] + str(self.api_version))
            self.modules += [module_class]
    
    def is_sup_cap(self, test):
        """Check if bridge supports the test module capability."""
        return test.test_module in self.sup_caps if test.test_module and self.sup_caps else True
    
    def __repr__(self):
        version_str = f", version={self.version}" if self.version else ""
        return f"Bridge(id={self.id_str}, board_type={self.board_type}{version_str})"

def cfg_brg_defaults_ret_after_fail(test):
    wlt_print(f"Configuring bridge {test.active_brg.id_str} to defaults\n", "BLUE")
    modules = test.active_brg.modules
    for module in modules:
        wlt_print(f"Configuring {module.__name__} to defaults", "BLUE")
        cfg_pkt = cert_config.get_default_brg_pkt(test, module)
        res = cert_config.brg_configure(test=test, cfg_pkt=cfg_pkt)[1]
        if res == NO_RESPONSE:
            wlt_print(f"FAILURE: {module.__name__} configuration to defaults\n", "RED")
            return NO_RESPONSE
        else:
            wlt_print(f"SUCCESS: {module.__name__} configured to defaults\n", "GREEN")
    return DONE

def handle_prep_brg_for_latest(test, interface, brg_id, start_time):
    if test.rc == TEST_FAILED:
        wlt_print(f"No ModuleIf pkts found, try again", "BLUE")
        test.rc = ""
        test, interface = cert_common.get_module_if_pkt(test)
    if test.rc == TEST_FAILED:
        error = f"ERROR: No ModuleIf pkts found for 2 tries, couldn't perform OTA for bridge"
        handle_error(error, start_time)
    version = f"{interface.major_ver}.{interface.minor_ver}.{interface.patch_ver}"
    board_type = interface.board_type
    wlt_print(f"BRG version [{version}], board type [{board_type}]", "BLUE")
    wlt_print(f"Skipping configurations for BRG {brg_id} to defaults because of latest/rc flag", "BLUE")
    return Bridge(brg_id, interface_pkt=interface)

# Check BRGs are online and configure to defaults
def ut_prep_brg(args, start_time, tester, brg_id, validation_schema, is_tester_brg=False):
    brg = Bridge(brg_id)
    wlt_print(SEP)
    if not cert_common.is_cert_running:
        versions_mgmt = load_module('versions_mgmt.py', f'{UTILS_BASE_REL_PATH}/versions_mgmt.py')
        brg_owner = versions_mgmt.gw_brg_owner(env=AWS, server=PROD, brg=brg.id_str)
        if brg_owner and not brg_owner in r_codes:
            wlt_print(f"WARNING: {brg} owned by account {brg_owner}")
    test = WltTest("", tester, dut=brg, exit_on_param_failure=args.exit_on_param_failure, data=args.data)
    wlt_print(f"Getting {brg} version and board type", "BLUE")
    test, interface = cert_common.get_module_if_pkt(test)
    # TODO - check validation against device response!
    if args.latest or args.rc:
        return handle_prep_brg_for_latest(test, interface, brg_id, start_time)
    elif test.rc == TEST_FAILED:
        error = f"ERROR: Didn't get ModuleIfV{test.active_brg.api_version} from BRG:{brg.id_str}!\nCheck that the brg responded with the correct module"
        handle_error(error, start_time)
    version = f"{interface.major_ver}.{interface.minor_ver}.{interface.patch_ver}"
    board_type = interface.board_type
    wlt_print(f"\nBRG version [{version}], board type [{board_type}]\n", "BLUE")
    # Set default values for max output power and dual polarization antenna per board type if is_tester_brg is True
    max_output_power = MAX_OUTPUT_POWER_PER_TESTER_BOARD_TYPE[board_type] if is_tester_brg else args.max_output_power
    dual_polarization_antenna = DUAL_POLARIZATION_ANTENNA_PER_TESTER_BOARD_TYPE[board_type] if is_tester_brg else args.dual_polarization_antenna
    test.active_brg = Bridge(brg.id_str, interface_pkt=interface, max_output_power_dbm=max_output_power, dual_polarization_antenna=dual_polarization_antenna, validation_schema=validation_schema)
    test.dut = test.active_brg
    modules_support = []
    for module_id in [m for m in ag.MODULES_DICT.keys() if m != ag.MODULE_IF]:
        modules_support.append([module_name_id2display(module_id), color("GREEN", "SUPPORTED") if module_id in test.active_brg.sup_caps else color("WARNING", "UNSUPPORTED")])
    wlt_print(f"BRG {brg.id_str} modules support coverage:", "BLUE")
    wlt_print(tabulate.tabulate(modules_support, headers=['Module', 'Support'], tablefmt="fancy_grid"))
    test.active_brg.board_type = board_type
    cfg_output = cfg_brg_defaults_ret_after_fail(test=test)[1]
    if cfg_output == NO_RESPONSE:
        error = f"ERROR: Didn't get response from BRG:{brg.id_str}!"
        handle_error(error, start_time)
    test, interface = cert_common.get_module_if_pkt(test)
    if test.rc == TEST_FAILED:
        error = f"ERROR: Didn't get ModuleIfV{test.active_brg.api_version} from BRG:{brg.id_str}!"
        handle_error(error, start_time)
    wlt_print(f"Received cfg hash {hex(interface.cfg_hash)}", "BLUE")
    if not interface.cfg_hash or len(str(interface.cfg_hash)) < BRG_CFG_HAS_LEN:
        error = f"ERROR: invalid cfg_hash for BRG:{brg.id_str}!"
        handle_error(error, start_time)
    wlt_print(f"BRG {brg.id_str} cfg_hash_default={hex(interface.cfg_hash)}", "BLUE")
    return Bridge(brg.id_str, interface_pkt=interface, max_output_power_dbm=max_output_power, dual_polarization_antenna=dual_polarization_antenna, validation_schema=validation_schema)

##################################
# Gateway
##################################
cloud_connectivity_flag = lambda validation_schema: 'properties' in validation_schema
class Gateway:
    def __init__(self, id_str="", gw_version=None, gw_api_version=GW_API_VER_LATEST, 
                 protobuf=False, mqttc=None, gw_sim=None, port='', 
                 internal_brg=None, gw_orig_versions=None, validation_schema=None, upload_wait_time=0):
        """
        Initialize a Gateway object.
        
        Args:
            id_str: Gateway ID string
            gw_version: Dictionary with BLE_VERSION and WIFI_VERSION keys
            gw_api_version: Gateway API version
            protobuf: Boolean indicating if gateway uses protobuf (default: False)
            mqttc: MQTT client for the gateway
            gw_sim: Gateway simulator thread (optional)
            port: Port number (optional)
            internal_brg: Internal Bridge object (optional)
            gw_orig_versions: Original gateway versions dictionary (optional)
            validation_schema: Validation schema dictionary
        """
        self.id_str = id_str
        self.gw_version = gw_version or {}
        self.gw_api_version = gw_api_version
        self.mqttc = mqttc
        self.gw_sim = gw_sim
        self.port = port
        self.internal_brg = internal_brg
        self.gw_orig_versions = gw_orig_versions or gw_version or {}
        self.protobuf = protobuf
        self.validation_schema = validation_schema
        self.upload_wait_time = upload_wait_time

    def __repr__(self):
        internal_brg_str = f", {self.internal_brg}" if self.internal_brg else ""
        return f"Gateway(id={self.id_str}, api_version={self.gw_api_version}{internal_brg_str})"
    
    def has_internal_brg(self):
        """Check if gateway has an internal bridge."""
        return self.internal_brg is not None
    
    def is_simulated(self):
        """Check if gateway is simulated."""
        return self.gw_sim is not None

def get_tester_id(tester):
    if not tester or tester == GW_SIM_PREFIX:
        return f"GW_SIM_{get_random_hex_str(12)}"
    else:
        # Allow tester to be specified as tester_id:ble_addr
        if ':' in tester:
            tester, _ = tester.split(':')
        return tester

def prep_dut(args, tester, validation_schema, mqttc, start_time, upload_wait_time, gw_api_version):
    """
    Prepare device under test - returns Gateway() or Bridge() object.
    
    Returns:
        Gateway object if device is a gateway (with optional internal Bridge)
        Bridge object if device is a standalone bridge
    """
    wlt_print(SEP + f"Preparing DUT with ID {args.dut}" + SEP, "BLUE")
    wlt_print(f"Setting GW API version accrding to user's input. GW API version: {gw_api_version}", "BLUE")
    if cloud_connectivity_flag(validation_schema):
        dut = Gateway(
            id_str=args.dut,
            gw_version=None,
            gw_api_version=gw_api_version,
            protobuf=False,
            mqttc=mqttc,
            internal_brg=None,
            gw_orig_versions=None,
            validation_schema=validation_schema['properties'],
            upload_wait_time=upload_wait_time
        )
        test = WltTest("", tester=None, dut=dut)
        test, gw_info_ble_addr = prep_gw_info_action(test=test, start_time=start_time, brg_flag=brg_flag(validation_schema), target=DUT)
        if brg_flag(validation_schema):
            if not args.combo_ble_addr:
                handle_error(f"ERROR: combo_ble_addr is missing! dut should be {args.dut}:<combo_ble_addr>", start_time)
            elif gw_info_ble_addr and gw_info_ble_addr != args.combo_ble_addr:
                handle_error(f"ERROR: DUT internal BRG ID from gw_info ({gw_info_ble_addr}) doesn't match the provided combo_ble_addr ({args.combo_ble_addr})!", start_time)

        test.dut.gw_orig_versions = test.dut.gw_version.copy()
        internal_brg_str = f":{args.combo_ble_addr}" if args.combo_ble_addr else ""
        wlt_print(f"Starting certification for {test.dut}{internal_brg_str}")
        # Prepare gateway's internal BRG
        if brg_flag(validation_schema):
            dut.internal_brg = ut_prep_brg(args, start_time, tester=test.dut, brg_id=args.combo_ble_addr, validation_schema=validation_schema['modules'])
            if dut.internal_brg.api_version < API_OLDEST_SUPPORTED_VERSION:
                 handle_error(f"ERROR: DUT internal brg FW api_version={dut.internal_brg.api_version} is lower then the oldest supported = {API_OLDEST_SUPPORTED_VERSION}! Please upgrade the internal brg FW!", start_time)
        # Return Gateway object
        return dut

    elif brg_flag(validation_schema):
        # Prepare standalone bridge using prepared tester
        brg = ut_prep_brg(args, start_time, tester=tester, brg_id=args.dut, validation_schema=validation_schema['modules'])
        if brg.api_version < API_OLDEST_SUPPORTED_VERSION:
            handle_error(f"ERROR: DUT brg FW api_version={brg.api_version} is lower then the oldest supported = {API_OLDEST_SUPPORTED_VERSION}! Please upgrade the brg FW!", start_time)
        return brg


def prep_tester(args, mqttc, start_time, tester_validation_schema, gw_sim_thread=None):
    """
    Prepare tester gateway - returns Gateway() object (can also be a simulated GW).
    
    Returns:
        Gateway object with optional internal Bridge
    """
    wlt_print(SEP + f"Preparing tester with ID {args.tester}" + SEP, "BLUE")
    tester = Gateway(
        id_str=args.tester,
        gw_version=None,
        gw_api_version=None,
        protobuf=False,
        mqttc=mqttc,
        gw_sim=gw_sim_thread,
        port=args.port,
        internal_brg=None,
        gw_orig_versions=None,
        validation_schema=tester_validation_schema['properties']
    )
    # Prepare a GW SIM tester
    if gw_sim_thread:
        # Check simulator is online and configure to defaults
        wlt_print("Checking UART response and configure internal brg to defaults", "BLUE")
        internal_brg_mac_addr = os.getenv(GW_SIM_BLE_MAC_ADDRESS)
        internal_brg_ble_ver = os.getenv(GW_APP_VERSION_HEADER)
        if not internal_brg_mac_addr:
            handle_error(f"ERROR: Didn't receive {GW_SIM_BLE_MAC_ADDRESS} response!", start_time)
        tester.gw_version = {BLE_VERSION:internal_brg_ble_ver, WIFI_VERSION:"0.0.0"}
        tester.gw_api_version = GW_API_VER_LATEST

    # Prepare a GW tester
    else:
        test = WltTest("", tester=tester, dut=None)
        test, internal_brg_mac_addr = prep_gw_info_action(test=test, start_time=start_time, brg_flag=True, target=TESTER)
        # Tester is expected to have ble addr in gw info response
        if internal_brg_mac_addr == "":
            handle_error(f"ERROR: internal_brg_mac_addr in response is empty!", start_time)
        test.tester.gw_orig_versions = test.tester.gw_version.copy()
        wlt_print(f"Starting certification with tester ID {test.tester.id_str} and tester's internal BRG ID {internal_brg_mac_addr}")
        # Configure GW to defaults
        if not args.latest and not args.rc:
            test, res = cert_config.config_gw_defaults(test, target=TESTER)
            if res == NO_RESPONSE:
                handle_error("ERROR: Config tester to defaults failed!", start_time)
        else:
            wlt_print(f"Skipping configurations for tester {tester} to defaults because of latest/rc flag", "BLUE")
        tester = test.tester

    # Prepare tester's internal BRG
    tester.internal_brg = ut_prep_brg(args, start_time, tester, internal_brg_mac_addr, validation_schema=tester_validation_schema['modules'], is_tester_brg=True)
    # Return Gateway object
    return tester

def prep_gw_info_action(test, start_time, brg_flag, target):
    gw = test.dut if target == DUT else test.tester
    wlt_print(f"Getting {gw} information", "BLUE")
    response = cert_common.get_gw_info(test, target=target)
    if response == NO_RESPONSE:
        error = f"ERROR: Didn't get response from {gw} !"
        handle_error(error, start_time)
    internal_brg_mac_addr = ""
    if ENTRIES in response[GW_INFO]:
        # Protobuf
        info = response[GW_INFO][ENTRIES]
        gw.protobuf = True
        if BLE_VERSION in info and WIFI_VERSION in info:
            gw.gw_version = {BLE_VERSION : info[BLE_VERSION][STR_VAL], WIFI_VERSION : info[WIFI_VERSION][STR_VAL]}
        if brg_flag and BLE_MAC_ADDR in info:
            internal_brg_mac_addr = info[BLE_MAC_ADDR][STR_VAL]
        if GW_API_VERSION in info:
            gw.gw_api_version = info[GW_API_VERSION][STR_VAL]
    else:
        # JSON
        info = response[GW_INFO]
        gw.protobuf = False
        if BLE_VERSION in info and WIFI_VERSION in info:
            gw.gw_version = {BLE_VERSION : info[BLE_VERSION], WIFI_VERSION : info[WIFI_VERSION]}
        if brg_flag and BLE_MAC_ADDR in info:
            internal_brg_mac_addr = info[BLE_MAC_ADDR]
        # For internal use only in versions update test 
        if GW_API_VERSION in info:
            gw.gw_api_version = info[GW_API_VERSION]

    if target == DUT:
        test.dut = gw
    else:
        test.tester = gw
    
    return test, internal_brg_mac_addr

