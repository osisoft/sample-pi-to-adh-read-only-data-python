"""This script tests the SDS Python sample script"""

from datetime import datetime, timedelta
import json
from typing import List
import unittest
import random
from adh_sample_library_preview import (ADHClient, SdsStream, SdsType, SdsTypeProperty, SdsTypeCode, SdsError)
from PIToOcsEvent import PIToOcsEvent
from program import main


class SDSPythonSampleTests(unittest.TestCase):
    """Tests for the SDS Python sample"""

    def test_main(self):
        """Tests the SDS Python main sample script"""
        # Create test data
        self.setup_data()

        # Test main program
        try:
            main(True)
        finally:
            # Clean up test data
            self.cleanup(self.namespace_id, self.type_id, self.stream_id)

    def get_appsettings(self):
        """Open and parse the appsettings.json file"""

        # Try to open the configuration file
        try:
            with open(
                'appsettings.json',
                'r',
            ) as f:
                appsettings = json.load(f)
        except Exception as error:
            print(f'Error: {str(error)}')
            print(f'Could not open/read appsettings.json')
            exit()

        return appsettings


    def create_type(self, type_id: str) -> SdsType:
        # Create types to be used in type properties
        datetime_type = SdsType('Datetime', SdsTypeCode.DateTime)
        nullable_type = SdsType('NullableSingle', SdsTypeCode.NullableSingle)
        boolean_type = SdsType('Boolean', SdsTypeCode.Boolean)
        string_type = SdsType('String', SdsTypeCode.String)
        nullable_int32_type = SdsType('NullableInt32', SdsTypeCode.NullableInt32)

        # Create type properties
        timestamp = SdsTypeProperty(id='Timestamp', name='Timestamp', is_key=True, sds_type=datetime_type)
        value = SdsTypeProperty(id='Value', name='Value', is_key=False, sds_type= nullable_type)
        is_questionable = SdsTypeProperty(id='IsQuestionable', name='IsQuestionable', is_key=False, sds_type=boolean_type)
        is_substituted = SdsTypeProperty(id='IsSubstituted', name='IsSubstituted', is_key=False, sds_type=boolean_type)
        is_annotated = SdsTypeProperty(id='IsAnnotated', name='IsAnnotated', is_key=False, sds_type=boolean_type)
        systemstate_code = SdsTypeProperty(id='SystemStateCode', name='SystemStateCode', is_key=False, sds_type=nullable_int32_type)
        digitalstate_name = SdsTypeProperty(id='DigitalStateName', name='DigitalStateName', is_key=False, sds_type=string_type)
        typeProperties = [timestamp, value, is_questionable, is_substituted, is_annotated, systemstate_code, digitalstate_name]

        # Create type
        testType = SdsType(id=type_id, name=type_id, sds_type_code=SdsTypeCode.Object, properties=typeProperties)
        return self.sds_client.Types.getOrCreateType(namespace_id=self.namespace_id, type=testType)
        

    def create_stream(self, stream_id: str, type_id: str) -> SdsStream:
        testStream = SdsStream(id=stream_id, type_id=type_id)
        self.sds_client.Streams.createOrUpdateStream(namespace_id=self.namespace_id, stream=testStream)


    def create_test_values(self) -> List[PIToOcsEvent]:
        # Get current time to create offset timestamps
        current_time = datetime.utcnow()

        # Normal event with positive Value
        event_value = PIToOcsEvent()
        event_value.Value = random.uniform(0, 100)
        event_value.Timestamp = current_time.isoformat()

        # Normal event with negative Value
        event_negative_value = PIToOcsEvent()
        event_negative_value.Value = random.uniform(0, -100)
        event_negative_value.Timestamp = (current_time - timedelta(seconds=1)).isoformat()

        # Event with IsQuestionable as true
        event_questionable = PIToOcsEvent()
        event_questionable.IsQuestionable = True
        event_questionable.Value = random.uniform(0, 100)
        event_questionable.Timestamp = (current_time - timedelta(seconds=2)).isoformat()

        # Event with SystemStateCode and no Value
        event_system_code = PIToOcsEvent()
        event_system_code.SystemStateCode = '246'
        event_system_code.DigitalStateName = 'I/O Timeout'
        event_system_code.Timestamp = (current_time - timedelta(seconds=3)).isoformat()

        return [event_value, event_negative_value, event_questionable, event_system_code]

    def cleanup(self, namespace_id: str, type_id: str, stream_id: str):
        try:
            print(f'Deleting created Type: {type_id} and Stream: {stream_id}')
            self.sds_client.Streams.deleteStream(namespace_id=namespace_id, stream_id=stream_id)
            self.sds_client.Types.deleteType(namespace_id=namespace_id, type_id=type_id)
            print('Done!')
        except SdsError as err:
            print('Failed Deletion with Message: ' + err.value)


    def setup_data(self):
        appsettings = self.get_appsettings()
        self.namespace_id = appsettings.get('NamespaceId')
        self.stream_id = appsettings.get('StreamId')
        self.type_id = appsettings.get('TypeId')

        self.sds_client = ADHClient(
            appsettings.get('ApiVersion'),
            appsettings.get('TenantId'),
            appsettings.get('Resource'),
            appsettings.get('ClientId'),
            appsettings.get('ClientSecret'))

        print('Get or create SDS Type and Stream to use') 
        type = self.create_type(type_id=self.type_id)
        self.create_stream(stream_id=self.stream_id, type_id=type.Id)

        print('Create and upload test values')
        values = self.create_test_values()
        self.sds_client.Streams.insertValues(namespace_id=self.namespace_id, stream_id=self.stream_id, values=values)

if __name__ == '__main__':
    unittest.main()
