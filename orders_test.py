from datetime import datetime, timedelta

import pytest
from pytest import mark

from zoetisqa.helpers import MenuHelper, Logger
from zoetisqa.helpers.api import PatientAPIHelper
from zoetisqa.helpers.api import TestsAPIHelper
from zoetisqa.helpers.constants import ResultStatusValues, SimulatorScenarios, ScenarioNumber, AnalyzerTests
from zoetisqa.helpers.patient import PatientHelper
from zoetisqa.helpers.results import ResultHelper
from zoetisqa.helpers.tests import TestProgressHelper, TestsHelper
from zoetisqa.models.clinic import Order, Patient, AnalyteResult


class TestOrders:

    @pytest.fixture(autouse=True)
    def setup(self, start_analyzers):
        Logger.info('Orders suite: Starting analyzers')

    @mark.opticell
    @mark.testcase(id='VSIC-T530')
    @mark.testcase(id='VSIC-T531')
    def test_create_order(self, hub_app):
        scenario = SimulatorScenarios.Scenarios.get(ScenarioNumber.S016)
        patient = Patient(animal_name=scenario.patient_name, species=scenario.species)
        test = AnalyzerTests.OPTICELL_HEMATOLOGY
        blood_count_test_row = self._create_test_order(patient=patient, test_order=test, use_api=True)
        assert blood_count_test_row[1].text == test
        assert blood_count_test_row[6].text == 'Start test'
        tests_helper = MenuHelper().tests_tab()
        progress_helper = tests_helper.click_start_test_from_all_tests(patient=patient, test=test)
        progress_helper.wait_test_to_complete()
        tests_menu = MenuHelper().tests_tab()
        tests_helper.wait_for_complete_test_status(patient=patient, test=test)
        test_row = tests_helper.get_row_in_all(patient=patient, test=test)
        assert test_row[5].text == ResultStatusValues.RESULTS
        progress_helper = tests_menu.click_view_details_from_all_tests(patient=patient, test=test)
        test_results = progress_helper.get_test_results_data()
        expected_result = ResultHelper().scenario_S016_result(patient=patient)
        assert test_results == expected_result
        assert len(test_results.analyzer_serial) > 3, 'Analyzer serial number is too short'
        assert test_results.status == ResultStatusValues.RESULTS, 'Status is incorrect'
        assert test_results.test == test, 'Test name is incorrect'
        assert test_results.result_id.startswith('HUB-'), 'Order ID does not start with "HUB-"'
        assert len(test_results.result_id) > 4, 'Order ID is too short'
        # Determine if the time format is 24-hours or not
        date_format = '%H:%M, %B %d, %Y'
        am_pm = (test_results.test_date.split(',')[0])[-2:]
        if am_pm == 'AM' or am_pm == 'PM':
            date_format = '%I:%M %p, %B %d, %Y'
        test_time = datetime.strptime(test_results.test_date, date_format)
        elapsed_time = abs(datetime.now() - test_time)
        assert elapsed_time <= timedelta(minutes=2), 'There is a long time elapsed between test time and now'
        assert test_results.warning_label == ('Warning : Abnormal distribution of PLT cell volumes is suspected. '
                                              'Blood smear review recommended.')
        patient = Patient()
        self._create_test_order(patient=patient, test_order=test)
        progress_helper = MenuHelper().tests_tab().click_start_test_from_all_tests(patient=patient, test=test)
        progress_helper.cancel_test()
        tests_helper = MenuHelper().tests_tab()
        tests_helper.wait_for_cancel_status(patient=patient, test=test)
        test_row = tests_helper.get_row_in_all(patient=patient, test=test)
        assert test_row[5].text == ResultStatusValues.CANCELLED

    @mark.vs2
    @mark.testcase(id='VSIC-T302')
    def test_create_vs2_order(self, hub_app):
        patient = Patient()
        test = AnalyzerTests.THYROXINE_T4_CHOLESTEROL_TEST
        test_row = self._create_test_order(patient=patient, test_order=test)
        assert test_row[1].text == test
        assert test_row[6].text == 'View details'
        serial = test_row[2].text
        device_helper = MenuHelper().mylab_tab().click_analyzer_card(serial=serial)
        test_row = device_helper.get_test(patient=patient, test=test)
        assert test_row[0].text.split('\n')[1] == patient.animal_id
        assert test_row[2].text == test
        patient_tab = MenuHelper().patients_tab()
        patient_tab.select_patient(patient=patient)
        test_row = patient_tab.get_current_test(test=test)
        assert test_row[0].text == test #
        assert test_row[2].text == ResultStatusValues.PENDING
        tests_menu = MenuHelper().tests_tab()
        progress_helper = tests_menu.click_view_details_from_all_tests(patient=patient, test=test)
        progress_helper.wait_test_to_complete()
        test_results = progress_helper.get_test_results_data()
        elapsed_time = abs(datetime.now() - test_results.test_datetime())
        assert elapsed_time <= timedelta(minutes=2), 'There is a long time elapsed between test time and now'
        assert test_results.status == ResultStatusValues.RESULTS, 'Status is incorrect' #Checks the result status is RESULTS
        expected_analyte = AnalyteResult(code='T4', unit='ug/dL', result='Normal', lower_range='1.5',
                                         upper_range='4.8', flag='Normal')
        assert test_results.analyte_results[0].compare_result_range(expected_analyte)
        expected_analyte = AnalyteResult(code='CHOL', unit='mg/dL', result='Normal', lower_range='90',
                                         upper_range='205', flag='Normal')
        assert test_results.analyte_results[1].compare_result_range(expected_analyte)

    @mark.vs2
    @mark.testcase(id='VSIC-2775')
    def test_unrequested_cancel_vs2(self, hub_app):
        test = AnalyzerTests.COMPREHENSIVE_DIAGNOSTIC
        self._cancel_unrequested_steps(test=test)

    @mark.hm5
    @mark.testcase(id='VSIC-2775')
    def test_unrequested_cancel_hm5(self, hub_app):
        test = AnalyzerTests.COMPLETE_BLOOD_COUNT
        self._cancel_unrequested_steps(test=test)

    def _cancel_unrequested_steps(self, test):
        patient = Patient(animal_name=f'{ScenarioNumber.S047};A130')
        self._create_test_order(patient=patient, test_order=test, use_api=True)
        progress_helper = TestsHelper().click_view_details_from_all_tests(patient=patient, test=test)
        progress_helper.wait_test_to_cancel()
        expected = ResultStatusValues.status_attributes[ResultStatusValues.CANCELLED][0]
        assert progress_helper.status_badge() == expected

    def disabled_test_opticell_qc(self, browser):
        """
         Need to add steps to create the Opticell QC test. The following works after you've manually obtained a QC
         result. This also needs to be expanded to confirm that all the "analytes" that we expect in a QC are there
         and give a "PASS" result. Also, the test name will be updated in the UI by HUB devs at some point.
         For now, this basically just tests that we can parse an Opticell QC result successfully, and it prints the list
         results which is a Python dict.
        """
        test = "tests.qc.norm.hmx"
        patient = ""
        tests_helper = MenuHelper().tests_tab()
        tests_helper.click_start_test_from_all_tests(patient, test)
        ResultHelper().parse_opticell_quality_control()

    def _create_test_order(self, patient: Patient, test_order, use_api=False, skip_create_patient=False):
        if use_api:
            PatientAPIHelper().create(patient=patient)
        elif not skip_create_patient:
            PatientHelper().create_patient(patient=patient)
        order = Order(patient=patient, tests=[test_order])
        tests_helper = MenuHelper().tests_tab()
        tests_helper.quick_test(order)
        return tests_helper.get_row_in_all(patient=patient, test=test_order)

    def execute_scenario_test(self, scenario=ScenarioNumber.S001, error=False):
        """
        This method can be used for executing a scenario test.
        This handles creating the test, getting the results, setting up the expected result, and comparing them.
        Input: scenario - the Simulator scenario to be called ex: S001
        error - True/False - whether the generated Sim result will be an error. This only affects the detection of the
        result and will not cause a test to fail. If it is incorrect for the test, it will wait for a 90 second timeout.
        """
        scenario_info = SimulatorScenarios.Scenarios.get(scenario)
        patient = Patient(animal_name=scenario_info.patient_name, species=scenario_info.species,)
        tests_helper = MenuHelper().tests_tab()
        self._create_test_order(patient=patient, test_order=scenario_info.test, use_api=True)
        tests_helper.click_start_test_from_all_tests(patient, scenario_info.test)
        progress_helper = TestProgressHelper()
        if error:
            progress_helper.wait_test_to_error()
        else:
            progress_helper.wait_test_to_complete()
        return patient, ResultHelper().load_to_labresult()

    @mark.vs2
    def test_scenario_S028(self, hub_app):
        patient, result = self.execute_scenario_test(scenario=ScenarioNumber.S028)
        expected_result = ResultHelper().scenario_S028_result(patient=patient)
        assert result == expected_result

    def test_date_from_pending_to_results (self, hub_app):
        date_on_pending = "Created at"
        date_on_results = "Done at"
        current_date = datetime.now().strftime("%m/%d/%Y")
        patient = PatientAPIHelper().create()
        test = AnalyzerTests.COMPLETE_BLOOD_COUNT
        test_code = AnalyzerTests.TEST_CODES[test]
        TestsAPIHelper().create(patient_id=patient.internal_id, test_code=test_code)

        # Validate Date&Time column when test status is Pending
        tests_helper = MenuHelper().tests_tab()
        test_row_pending = tests_helper.search_test_list(query=patient.animal_id)
        tests_helper.wait_for_pending_test_status(patient=patient, test=test)
        assert test_row_pending[5].text == "Pending"
        text_lines = test_row_pending[4].text.split('\n')
        assert text_lines[0] == date_on_pending, f"Expected first line '{date_on_pending}' but got '{text_lines[0]}'"
        date_part = text_lines[-1].split(',')[-1].strip()
        assert date_part == current_date, f"Expected date '{current_date}' but got '{date_part}'"

        # Validate Date&Time column when test status is Results
        tests_helper.wait_for_complete_test_status(patient=patient, test=test)
        test_row_results = tests_helper.search_test_list(query=patient.animal_id)
        assert test_row_results[5].text == "Results"
        text_lines = test_row_results[4].text.split('\n')
        assert text_lines[0] == date_on_results, f"Expected first line '{date_on_results}' but got '{text_lines[0]}'"
        date_part = text_lines[-1].split(',')[-1].strip()
        assert date_part == current_date, f"Expected date '{current_date}' but got '{date_part}'"
