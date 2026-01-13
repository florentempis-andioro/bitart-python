import base64
import yaml

def crunch64(s):
    if isinstance(s, str):
        s = s.encode('utf-8')
    # Ruby: urlsafe_encode64(str, padding: false)
    # Python: urlsafe_b64encode returns bytes. Padding might be present.
    # We need to strip padding '='
    encoded = base64.urlsafe_b64encode(s).decode('ascii')
    return encoded.rstrip('=')

def safe_yaml_dump(obj):
    return yaml.dump(obj, default_flow_style=False)
