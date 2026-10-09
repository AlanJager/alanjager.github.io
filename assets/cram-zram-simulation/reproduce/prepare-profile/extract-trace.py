from pathlib import Path
import base64,gzip
root=Path(__file__).resolve().parent
s=(root/'guest-boot.log').read_text().replace('\r','')
encoded=s.split('TRACE_GZIP_BASE64_BEGIN\n',1)[1].split('TRACE_GZIP_BASE64_END',1)[0]
(root/'move.trace').write_bytes(gzip.decompress(base64.b64decode(encoded)))
