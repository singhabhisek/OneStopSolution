import os
import xml.etree.ElementTree as ET
import zipfile
from urllib.parse import urlparse
import sys
def extract_sessions_from_saz(saz_file_path, allowed_hosts, skip_file_types ):
    sessions = {}

    try:
        with zipfile.ZipFile(saz_file_path, 'r') as saz_file:
            for file_info in saz_file.infolist():
                if file_info.filename.endswith('_c.txt'):
                    session_id = file_info.filename.replace('_c.txt', '')
                    try:
                        with saz_file.open(file_info) as file:
                            session_data = file.read().decode('utf-8')

                            if any(ext in session_data.lower() for ext in skip_file_types):
                                print(f"Skipping session {session_id} due to file type ")
                                continue

                            # Extract hostname from _c.txt session data
                            lines = session_data.split('\n')
                            host_line = next((line for line in lines if line.lower().startswith('host:')), None)
                            if not host_line:
                                print(f"Skipping session {session_id} due to missing Host header.")
                                continue

                            host = host_line.split(':')[1].strip()
                            if host not in allowed_hosts:
                                print(f"Skipping session {session_id} due to not being an allowed host.")
                                continue

                            sessions[session_id] = {'data': session_data, 'comment': '', 'status_code': None}
                    except UnicodeDecodeError:
                        print(f"Error decoding session {session_id}. Skipping this session.")
                        continue

                elif file_info.filename.endswith('_m.xml') or file_info.filename.endswith('_s.txt'):
                    session_id = file_info.filename.replace('_m.xml', '').replace('_s.txt', '')
                    if session_id not in sessions:
                        continue

                    if file_info.filename.endswith('_m.xml'):
                        with saz_file.open(file_info) as file:
                            xml_data = file.read().decode('utf-8')
                            root = ET.fromstring(xml_data)
                            ui_comment_element = root.find(".//SessionFlag[@N='ui-comments']")
                            ui_comment = ui_comment_element.get('V') if ui_comment_element is not None else ''
                            sessions[session_id]['comment'] = ui_comment

                    elif file_info.filename.endswith('_s.txt'):
                        with saz_file.open(file_info, 'r') as file:
                            lines = file.readlines()
                            status_line = lines[0].decode('utf-8').strip()
                            status_code = status_line.split(' ')[1]
                            sessions[session_id]['status_code'] = status_code

    except Exception as e:
        print(f"Error extracting sessions from SAZ file: {e}")

    return sessions


def parse_fiddler_session(session_data):
    try:
        lines = session_data['data'].strip().split('\r\n')
        request_line_parts = lines[0].split(' ')
        request_method = request_line_parts[0]
        url = request_line_parts[1]
        headers = {}
        body_start = False
        body = ''
        comment = session_data['comment']
        status_code = session_data.get('status_code', None)

        for line in lines[1:]:
            if line.strip() == '':
                body_start = True
                continue
            if body_start:
                body += line + '\n'
            else:
                if line.startswith("Comment:"):
                    comment = line.split(":")[1].strip()
                else:
                    key, value = line.split(':', 1)
                    headers[key.strip()] = value.strip()

        return request_method, url, headers, body.strip(), comment, status_code
    except Exception as e:
        print(f"Error parsing fiddler session: {e}")
        return None, None, None, None, None, None

def parse_url(url):
    try:
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.split(':')[0]
        path = parsed_url.path
        return domain, path
    except Exception as e:
        print(f"Error parsing URL: {e}")
        return None, None


def generate_jmeter_test_plan(sessions, allowed_hosts, allowed_status_codes, saz_file_name):

    try:
        # Create the main JMeter test plan
        test_plan = ET.Element('jmeterTestPlan', version="1.2", properties="5.0", jmeter="5.5")

        # Add hashTree after jmeterTestPlan
        hash_tree_main = ET.SubElement(test_plan, 'hashTree')

        # Add Test Plan configuration
        test_plan_elem = ET.SubElement(hash_tree_main, 'TestPlan', guiclass="TestPlanGui", testclass="TestPlan",
                                       testname=f"Test Plan", enabled="true")
        ET.SubElement(test_plan_elem, 'stringProp', name="TestPlan.comments")
        ET.SubElement(test_plan_elem, 'boolProp', name="TestPlan.functional_mode").text = "false"
        ET.SubElement(test_plan_elem, 'boolProp', name="TestPlan.tearDown_on_shutdown").text = "true"
        ET.SubElement(test_plan_elem, 'boolProp', name="TestPlan.serialize_threadgroups").text = "false"
        user_defined_vars = ET.SubElement(test_plan_elem, 'elementProp', name="TestPlan.user_defined_variables",
                                          elementType="Arguments", guiclass="ArgumentsPanel", testclass="Arguments",
                                          testname="User Defined Variables", enabled="true")
        ET.SubElement(user_defined_vars, 'collectionProp', name="Arguments.arguments")
        ET.SubElement(test_plan_elem, 'stringProp', name="TestPlan.user_define_classpath")

        # Add hashTree after TestPlan and before ThreadGroup
        hash_tree_after_test_plan = ET.SubElement(hash_tree_main, 'hashTree')

        # Add Thread Group
        thread_group = ET.SubElement(hash_tree_after_test_plan, 'ThreadGroup', guiclass="ThreadGroupGui", testclass="ThreadGroup",
                                      testname="Thread Group", enabled="true")
        ET.SubElement(thread_group, 'stringProp', name="ThreadGroup.on_sample_error").text = "continue"
        loop_controller = ET.SubElement(thread_group, 'elementProp', name="ThreadGroup.main_controller",
                                        elementType="LoopController", guiclass="LoopControlPanel",
                                        testclass="LoopController", testname="Loop Controller", enabled="true")
        ET.SubElement(loop_controller, 'boolProp', name="LoopController.continue_forever").text = "false"
        ET.SubElement(loop_controller, 'stringProp', name="LoopController.loops").text = "1"
        ET.SubElement(thread_group, 'stringProp', name="ThreadGroup.num_threads").text = "1"
        ET.SubElement(thread_group, 'stringProp', name="ThreadGroup.ramp_time").text = "1"
        ET.SubElement(thread_group, 'boolProp', name="ThreadGroup.scheduler").text = "false"
        ET.SubElement(thread_group, 'boolProp', name="ThreadGroup.same_user_on_next_iteration").text = "true"

        # Create hash tree for samplers
        hash_tree_for_samplers = ET.SubElement(hash_tree_after_test_plan, 'hashTree')

        current_transaction_controller = None
        last_comment = None

        for session_id, session_data in sessions.items():
            request_method, url, headers, body, comment, status_code = parse_fiddler_session(session_data)
            domain, path = parse_url(url)

            # Filter sessions based on allowed hosts and status codes
            if domain not in allowed_hosts or (allowed_status_codes and session_data['status_code'] not in allowed_status_codes):
                continue

            # Check if comment has changed to create a new TransactionController
            if comment != last_comment:
                if current_transaction_controller is not None:
                    pass

                # Create a new TransactionController
                current_transaction_controller = ET.SubElement(hash_tree_for_samplers, 'TransactionController',
                                                               guiclass="TransactionControllerGui",
                                                               testclass="TransactionController", testname=comment,
                                                               enabled="true")
                ET.SubElement(current_transaction_controller, 'boolProp',
                              name="TransactionController.includeTimers").text = "false"
                ET.SubElement(current_transaction_controller, 'boolProp',
                              name="TransactionController.parent").text = "false"
                hash_tree_for_transaction = ET.SubElement(hash_tree_for_samplers, 'hashTree')

            # Create HTTPSamplerProxy
            http_sampler = ET.SubElement(hash_tree_for_transaction, 'HTTPSamplerProxy',
                                         guiclass="HttpTestSampleGui", testclass="HTTPSamplerProxy",
                                         testname=f"HTTP Request - {comment}", enabled="true")
            # ET.SubElement(http_sampler, 'elementProp', name="HTTPsampler.Arguments", elementType="Arguments",
            #               guiclass="HTTPArgumentsPanel", testclass="Arguments", testname="User Defined Variables",
            #               enabled="true")

            if request_method == 'POST':
                ET.SubElement(http_sampler, 'boolProp', name="HTTPSampler.postBodyRaw").text = "true"
                arguments = ET.SubElement(http_sampler, 'elementProp', name="HTTPsampler.Arguments",
                                          elementType="Arguments")
                collection_prop = ET.SubElement(arguments, 'collectionProp', name="Arguments.arguments")
                arg_element = ET.SubElement(collection_prop, 'elementProp', name="", elementType="HTTPArgument")
                ET.SubElement(arg_element, 'boolProp', name="HTTPArgument.always_encode").text = "false"
                ET.SubElement(arg_element, 'stringProp', name="Argument.value").text = body
                ET.SubElement(arg_element, 'stringProp', name="Argument.metadata").text = "="

            # Set properties for HTTPSamplerProxy
            if domain:
                ET.SubElement(http_sampler, 'stringProp', name="HTTPSampler.domain").text = domain
            if url.startswith('http://'):
                ET.SubElement(http_sampler, 'stringProp', name="HTTPSampler.port").text = "80"
                ET.SubElement(http_sampler, 'stringProp', name="HTTPSampler.protocol").text = "http"
            else:
                ET.SubElement(http_sampler, 'stringProp', name="HTTPSampler.port").text = "443"
                ET.SubElement(http_sampler, 'stringProp', name="HTTPSampler.protocol").text = "https"

            ET.SubElement(http_sampler, 'stringProp', name="HTTPSampler.path").text = path
            ET.SubElement(http_sampler, 'stringProp', name="HTTPSampler.method").text = request_method
            ET.SubElement(http_sampler, 'boolProp', name="HTTPSampler.follow_redirects").text = "true"
            ET.SubElement(http_sampler, 'boolProp', name="HTTPSampler.auto_redirects").text = "false"
            ET.SubElement(http_sampler, 'boolProp', name="HTTPSampler.use_keepalive").text = "true"
            ET.SubElement(http_sampler, 'boolProp', name="HTTPSampler.DO_MULTIPART_POST").text = "false"

            # Add hashTree after each HTTPSamplerProxy
            ET.SubElement(hash_tree_for_transaction, 'hashTree')

            last_comment = comment

        # Close the last hashTree for TransactionController
        if current_transaction_controller is not None:
            pass

        # Write the XML to file
        jmx_file_path = os.path.join(os.path.dirname(saz_file_path),
                                     f"{os.path.splitext(os.path.basename(saz_file_path))[0]}.jmx")
        tree = ET.ElementTree(test_plan)
        tree.write(jmx_file_path, encoding="utf-8", xml_declaration=True)
    except Exception as e:
        print(f"Error generating JMeter test plan: {e}")



if __name__ == "__main__":
    saz_file_path = sys.argv[1]


    # List of allowed hosts
    allowed_hosts = ["www.demoblaze.com","api.demoblaze.com", "www.blazedemo.com"]
    # List of allowed status codes
    allowed_status_codes = ["200", "302"]
    # skip file type
    skip_file_types = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.ico', '.css', '.js', '.woff', '.woff2', '.ttf',
                       '.otf', '.svg']

    sessions = extract_sessions_from_saz(saz_file_path,allowed_hosts, skip_file_types)
    generate_jmeter_test_plan(sessions, allowed_hosts, allowed_status_codes, saz_file_path)

    print("JMeter test plan generated successfully!")
