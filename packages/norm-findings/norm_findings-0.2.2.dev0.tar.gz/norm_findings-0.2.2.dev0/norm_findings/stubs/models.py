import datetime

class RelatedSet:
    def all(self): return []
    def filter(self, *args, **kwargs): return self
    def count(self): return 0
    def first(self): return None
    def exists(self): return False

class Finding:
    # Class attributes required for AppCheck parser introspection
    unique_id_from_tool = None
    cvssv3 = None
    epss_score = None
    title = ""
    description = ""
    mitigation = ""
    impact = ""
    references = ""
    severity = "Info"
    unsaved_vulnerability_ids = None
    unsaved_endpoints = []
    
    def __init__(self, **kwargs):
        self.unsaved_vulnerability_ids = None
        self.unsaved_endpoints = []
        self.cwe = 0
        self.date = datetime.date.today()
        self.active = True
        self.verified = False
        self.false_p = False
        self.duplicate = False
        self.out_of_scope = False
        self.risk_accepted = False
        self.under_review = False
        self.numerical_severity = "S5"
        self.description = ""
        self.mitigation = ""
        self.impact = ""
        self.references = ""
        self.severity = "Info"
        self.severity = "Info"
        self.title = ""
        self.unique_id_from_tool = None
        
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __getattr__(self, name):
        if name.endswith('_set'):
            return RelatedSet()
        # Return None for missing attributes to avoid AttributeError in some parsers
        return None

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return self.__str__()
    
    SEVERITIES = {'Info': 4, 'Low': 3, 'Medium': 2, 'High': 1, 'Critical': 0}

    @staticmethod
    def get_numerical_severity(severity):
        if severity == "Critical":
            return "S0"
        if severity == "High":
            return "S1"
        if severity == "Medium":
            return "S2"
        if severity == "Low":
            return "S3"
        if severity == "Info":
            return "S4"
        return "S5"

class Endpoint:
    def __init__(self, **kwargs):
        self.host = ""
        self.protocol = None
        self.port = None
        self.path = None
        self.query = None
        self.fragment = None
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __str__(self):
        return f"{self.protocol or ''}://{self.host or ''}:{self.port or ''}{self.path or ''}"

    def __repr__(self):
        return self.__str__()

    def __getattr__(self, name):
        if name.endswith('_set'):
            return RelatedSet()
        return None

    @staticmethod
    def from_uri(uri):
        from urllib.parse import urlparse
        parsed = urlparse(uri)
        return Endpoint(
            protocol=parsed.scheme,
            host=parsed.hostname,
            port=parsed.port,
            path=parsed.path,
            query=parsed.query,
            fragment=parsed.fragment
        )

class Product:
    def __init__(self, name="Default Product", id=1):
        self.name = name
        self.id = id
    def __getattr__(self, name):
        if name.endswith('_set'):
            return RelatedSet()
        return None
    def __str__(self): return self.name
    def __repr__(self): return self.name

class Test:
    class Engagement:
        def __init__(self, product):
            self.product = product
        def __str__(self):
            return f"{self.product}"
        def __repr__(self):
            return f"{self.product}"
        def __getattr__(self, name):
            if name.endswith('_set'):
                return RelatedSet()
            return None

    def __init__(self, product=None):
        if product is None:
            product = Product()
        elif isinstance(product, str):
            product = Product(name=product)
        self.engagement = Test.Engagement(product)
        self.scan_type = ""
        self.title = ""
        self.description = ""
        self.api_scan_configuration = None
    
    def __str__(self):
        return f"{self.engagement.product}"
    
    def __repr__(self):
        return f"{self.engagement.product}"

    def __getattr__(self, name):
        if name.endswith('_set'):
            return RelatedSet()
        return None

class User:
    def __getattr__(self, name):
        if name.endswith('_set'):
            return RelatedSet()
        return None

# Add other stubs as needed by parsers
class Dojo_User: pass
class Dojo_Group: pass
class Role: pass
class Product_Type: pass
class Engagement: pass
class Development_Environment: pass
class Test_Type: pass

# Additional stubs found during E2E testing
class Product_API_Scan_Configuration: pass
class Sonarqube_Issue: pass
class Endpoint_Status:
    def __init__(self, *args, **kwargs):
        pass
class Endpoint_Status_Type: pass
class FileUpload: pass

SEVERITIES = Finding.SEVERITIES
