# Converted from DefectDojo parser
import typing
import datetime
# Required stubs: 

import collections
import csv
import io

class IntSightsCSVParser():

    def _parse_csv(self, csv_file) -> [dict]:
        '\n\n        Parses entries from the CSV file object into a list of alerts\n        Args:\n            csv_file: The JSON file object to parse\n        Returns:\n            A list of alerts [dict()]\n\n        '
        default_keys = ['Alert ID', 'Title', 'Description', 'Severity', 'Type', 'Source Date (UTC)', 'Report Date (UTC)', 'Network Type', 'Source URL', 'Source Name', 'Assets', 'Tags', 'Assignees', 'Remediation', 'Status', 'Closed Reason', 'Additional Info', 'Rating', 'Alert Link']
        required_keys = ['alert_id', 'title', 'severity', 'status']
        alerts = []
        invalid_alerts = []
        content = csv_file.read()
        if isinstance(content, bytes):
            content = content.decode('utf-8')
        csv_reader = csv.DictReader(io.StringIO(content), delimiter=',', quotechar='"')
        if (collections.Counter(default_keys) == collections.Counter(csv_reader.fieldnames)):
            default_valud = 'None provided'
            for alert in csv_reader:
                alert['alert_id'] = alert.pop('Alert ID')
                alert['title'] = alert.pop('Title')
                alert['description'] = alert.pop('Description')
                alert['severity'] = alert.pop('Severity')
                alert['type'] = alert.pop('Type')
                alert['source_date'] = alert.pop('Source Date (UTC)', default_valud)
                alert['report_date'] = alert.pop('Report Date (UTC)', default_valud)
                alert['network_type'] = alert.pop('Network Type', default_valud)
                alert['source_url'] = alert.pop('Source URL', default_valud)
                alert['assets'] = alert.pop('Assets', default_valud)
                alert['tags'] = alert.pop('Tags', default_valud)
                alert['status'] = alert.pop('Status', default_valud)
                alert['alert_link'] = alert.pop('Alert Link')
                alert.pop('Assignees')
                alert.pop('Remediation')
                alert.pop('Closed Reason')
                alert.pop('Rating')
                invalid_alerts.extend((alert for key in required_keys if (not alert[key])))
                if (alert not in invalid_alerts):
                    alerts.append(alert)
        else:
            self._LOGGER.error('The CSV file has one or more missing or unexpected header values')
        return alerts
