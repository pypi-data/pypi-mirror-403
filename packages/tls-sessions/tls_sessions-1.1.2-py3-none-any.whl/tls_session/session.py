import ctypes
import os
import json
import warnings
import random
import sys
sys.tracebacklimit = 0
# ------------------------------------------------------------------

warnings.filterwarnings("ignore")

_current_dir = os.path.dirname(os.path.abspath(__file__))
lib_path = os.path.join(_current_dir, "http2_bridge.so")
if not os.path.exists(lib_path):
	lib_path = os.path.join(_current_dir, "http2_bridge.dll")

lib = ctypes.CDLL(lib_path)

lib.DoRequest.argtypes = [
	ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, # method, url, headers
	ctypes.c_char_p, ctypes.c_char_p,                 # body, fpKey
	ctypes.c_char_p,                                  # proxy
	ctypes.c_int, ctypes.c_int,                       # timeout, redirects
	ctypes.POINTER(ctypes.c_int)                      # resLen
]
lib.DoRequest.restype = ctypes.POINTER(ctypes.c_ubyte)


browsers = ['CHROME_64', 'CHROME_65', 'CHROME_66', 'CHROME_67', 'CHROME_68', 'CHROME_69', 'CHROME_70', 'CHROME_71', 'CHROME_72', 'CHROME_73', 'CHROME_74', 'CHROME_75', 'CHROME_76', 'CHROME_77', 'CHROME_78', 'CHROME_79', 'CHROME_80', 'CHROME_81', 'CHROME_82', 'CHROME_83', 'CHROME_84', 'CHROME_85', 'CHROME_86', 'CHROME_87', 'CHROME_88', 'CHROME_89', 'CHROME_90', 'CHROME_91', 'CHROME_92', 'CHROME_93', 'CHROME_94', 'CHROME_95', 'CHROME_96', 'CHROME_97', 'CHROME_98', 'CHROME_99', 'CHROME_100', 'CHROME_101', 'CHROME_102', 'CHROME_103', 'CHROME_104', 'CHROME_105', 'CHROME_106', 'CHROME_107', 'CHROME_108', 'CHROME_109', 'CHROME_110', 'CHROME_111', 'CHROME_112', 'CHROME_113', 'CHROME_114', 'CHROME_115', 'CHROME_116', 'CHROME_117', 'CHROME_118', 'CHROME_119', 'CHROME_120', 'CHROME_121', 'CHROME_122', 'CHROME_123', 'CHROME_124', 'CHROME_125', 'CHROME_126', 'CHROME_127', 'CHROME_128', 'CHROME_129', 'CHROME_130', 'CHROME_131', 'CHROME_132', 'CHROME_133', 'CHROME_134', 'CHROME_135', 'CHROME_136', 'CHROME_137', 'CHROME_138', 'CHROME_139', 'CHROME_140', 'CHROME_141', 'CHROME_142', 'CHROME_143','CHROME_144']
__all__  = ["Session","browsers"]

class UnknownError(Exception): pass
error_codes = {
	"200": { "message": "OK", "exception": "" },
	"201": { "message": "Created", "exception": "" },
	"202": { "message": "Accepted", "exception": "" },
	"204": { "message": "No Content", "exception": "" },
	"301": { "message": "Moved Permanently", "exception": "RedirectionError" },
	"302": { "message": "Found", "exception": "RedirectionError" }}

class Response:
	def __init__(self, data):
		self.status_code = data.get("status_code")
		self.headers = data.get("headers", {})
		self.text = data.get("body", "")
		self.error = data.get("error")
	def json(self): return json.loads(self.text)
	def __repr__(self): return f"<Response [{self.status_code}]>"

class Session:
	def __init__(self, fingerprint="CHROME_144", proxies=None):
		self.proxies  = proxies or ""
		if fingerprint.lower()=="auto":self.fp_key = random.choice(fingerprint.upper())
		elif not fingerprint.upper() in browsers:raise ValueError(f"Invalid chrome version, supported chrome versions : {browsers}")
		else:self.fp_key = fingerprint.upper()
		self.headers = {
			"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
			"Accept-Language": "en-US,en;q=0.9",
			"Cache-Control": "max-age=0",
			"Upgrade-Insecure-Requests": "1"
		}

	def _request(self, method, url, headers=None, data=None, json_payload=None, timeout=30, allow_redirects=True, proxies=None):
		current_headers = self.headers.copy()
		if headers: current_headers.update(headers)

		proxy_str = proxies if proxies else self.proxies
		body_str = json.dumps(json_payload) if json_payload else (str(data) if data else "")
		if json_payload: current_headers["Content-Type"] = "application/json"

		res_len = ctypes.c_int()
		ptr = lib.DoRequest(
			method.upper().encode(),
			url.encode(),
			json.dumps(current_headers).encode(),
			body_str.encode(),
			self.fp_key.encode(),
			proxy_str.encode(),
			int(timeout),
			1 if allow_redirects else 0,
			ctypes.byref(res_len)
		)

		raw_data = ctypes.string_at(ptr, res_len.value)
		lib.FreePointer(ptr)
		resp_data = json.loads(raw_data)
		
		rc = str(resp_data.get("status_code"))
		if rc not in error_codes:
			raise UnknownError(resp_data["body"].replace("utls","tls_session"))
		else:return Response(resp_data)

	def get(self, url, **kwargs): return self._request("GET", url, **kwargs)
	def post(self, url, **kwargs): return self._request("POST", url, **kwargs)
	def put(self, url, **kwargs): return self._request("PUT", url, **kwargs)
	def delete(self, url, **kwargs): return self._request("DELETE", url, **kwargs)


