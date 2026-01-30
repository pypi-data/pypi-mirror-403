# Converted from DefectDojo parser
import typing
import datetime
# Required stubs: 

import json

class IntSightsJSONParser():

    def _parse_json(self, json_file) -> [dict]:
        '\n        Parses entries from the JSON object into a list of alerts\n        Args:\n            json_file: The JSON file object to parse\n        Returns:\n            A list of alerts [dict()]\n        '
        alerts = []
        original_alerts = json.load(json_file)
        for original_alert in original_alerts.get('Alerts', []):
            alert = {}
            alert['alert_id'] = original_alert['_id']
            alert['title'] = original_alert['Details']['Title']
            alert['description'] = original_alert['Details']['Description']
            alert['severity'] = original_alert['Details']['Severity']
            alert['type'] = original_alert['Details']['Type']
            alert['source_date'] = original_alert['Details']['Source'].get('Date', 'None provided')
            alert['report_date'] = original_alert.get('FoundDate', 'None provided')
            alert['network_type'] = original_alert['Details']['Source'].get('NetworkType')
            alert['source_url'] = original_alert['Details']['Source'].get('URL')
            alert['assets'] = ','.join([item.get('Value') for item in original_alert['Assets']])
            alert['tags'] = original_alert['Details'].get('Tags')
            alert['status'] = ('Closed' if original_alert['Closed'].get('IsClosed') else 'Open')
            alert['alert_link'] = f"https://dashboard.intsights.com/#/threat-command/alerts?search={original_alert['_id']}"
            alerts.append(alert)
        return alerts
