"""
Changes:
1. Added requests.Session with connection pooling (~5x faster)
2. Added timeout on all requests (default 120s)
3. Fixed compression='zip' → 'bz2' bug for bzip content
4. Added automatic retry on 429/5xx errors

Usage:
    # Use: import ivolatility as ivol
"""

import logging
from datetime import datetime
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import pandas as pd
import time
from io import BytesIO 
import os

# ============================================================
# LOGGING CONFIGURATION - Detailed API request logging
# ============================================================
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Create logs directory if not exists
log_dir = 'logs'
os.makedirs(log_dir, exist_ok=True)

# File handler - incremental append mode with timestamps
log_file = os.path.join(log_dir, 'ivolatility_api.log')
file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
file_handler.setLevel(logging.DEBUG)

# Console handler - only warnings and errors
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.WARNING)

# Formatter with timestamp, level, and message
formatter = logging.Formatter(
    '%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Add handlers
logger.addHandler(file_handler)
logger.addHandler(console_handler)

logger.info("="*80)
logger.info("IVolatility API Logger Initialized")
logger.info("="*80)
    
__username__ = None
__password__ = None
__token__    = None
__auth__     = None

__delayBetweenRequests__ = 0.25
__fileDownloadTimeout__  = 600.0
__requestTimeout__ = 120.0  # Timeout for single request (2 minutes)

restApiURL = 'https://restapi.ivolatility.com'

# ============================================================
# SESSION WITH CONNECTION POOLING (MAIN OPTIMIZATION)
# ============================================================
# Reuses TCP connections + TLS sessions across requests
# Before: 24 requests × 500ms TLS handshake = 12 seconds
# After:  1 × 500ms + 23 × 100ms = 2.8 seconds (~5x faster)
# ============================================================

_session = requests.Session()

_retry_strategy = Retry(
    total=3,                                    # Max 3 retries
    backoff_factor=1,                           # Wait 1s, 2s, 4s between retries
    status_forcelist=[429, 500, 502, 503, 504], # Retry on these HTTP codes
    allowed_methods=["GET", "POST", "DELETE"]   # Retry these methods
)

_adapter = HTTPAdapter(
    pool_connections=10,   # Number of connection pools
    pool_maxsize=10,       # Max connections per pool
    max_retries=_retry_strategy
)

_session.mount("https://", _adapter)
_session.mount("http://", _adapter)

# Diagnostic counter
_request_count = 0

def get_request_count():
    """Get number of HTTP requests made through session"""
    return _request_count

def reset_request_count():
    """Reset request counter"""
    global _request_count
    _request_count = 0


class Auth(requests.auth.AuthBase):
    def __init__(self, apiKey):
        self.apiKey = apiKey
    def __call__(self, r):
        r.headers["apiKey"] = self.apiKey
        return r


def setRestApiURL(url):
    global restApiURL
    restApiURL = url


def getDelayBetweenRequests():
    global __delayBetweenRequests__
    return __delayBetweenRequests__

    
def setDelayBetweenRequests(value):
    global __delayBetweenRequests__
    __delayBetweenRequests__ = value

    
def getFileDownloadTimeout():
    global __fileDownloadTimeout__
    return __fileDownloadTimeout__

    
def setFileDownloadTimeout(value):
    global __fileDownloadTimeout__
    __fileDownloadTimeout__ = value


def getRequestTimeout():
    """Get timeout for single HTTP request (seconds)"""
    global __requestTimeout__
    return __requestTimeout__


def setRequestTimeout(value):
    """Set timeout for single HTTP request (seconds)"""
    global __requestTimeout__
    __requestTimeout__ = value

    
def getToken(username, password):
    logger.info(f"[AUTH] Getting token for user: {username}")
    response = _session.get(
        restApiURL + '/token/get', 
        params={'username': username, 'password': password},
        timeout=__requestTimeout__
    )
    logger.info(f"[AUTH] Token received: {response.text[:20]}...")
    return response.text


def createApiKey(nameKey, username, password):
    logger.info(f"[AUTH] Creating API key: {nameKey} for user: {username}")
    response = _session.post(
        restApiURL + '/keys?nameKey={}'.format(nameKey), 
        json={'username': username, 'password': password},
        timeout=__requestTimeout__
    )
    key = response.json()['key']
    logger.info(f"[AUTH] API key created: {key[:20]}...")
    return key

    
def deleteApiKey(nameKey, username, password):
    logger.info(f"[AUTH] Deleting API key: {nameKey} for user: {username}")
    response = _session.delete(
        restApiURL + '/keys?nameKey={}'.format(nameKey), 
        json={'username': username, 'password': password},
        timeout=__requestTimeout__
    )
    success = response.status_code == 200
    logger.info(f"[AUTH] API key deletion: {'SUCCESS' if success else 'FAILED'}")
    return success

    
def setLoginParams(username=None, password=None, token=None, apiKey=None):
    global __username__
    global __password__
    global __token__
    global __auth__
    
    __username__ = username
    __password__ = password
    __token__    = token
    __auth__     = None
    
    auth_method = []
    if apiKey is not None:
        __auth__ = Auth(apiKey)
        auth_method.append(f"apiKey: {apiKey[:20]}...")
    if token is not None:
        auth_method.append(f"token: {token[:20]}...")
    if username is not None:
        auth_method.append(f"user: {username}")
    
    logger.info(f"[AUTH] Login params set: {', '.join(auth_method) if auth_method else 'None'}")


def __raiseFileDownloadTimeout(start, fileDownloadTimeout, endpoint, urlForDetails):
    elapsed = (datetime.now() - start).total_seconds()
    if elapsed >= fileDownloadTimeout:
        logger.error(f"[TIMEOUT] File download timeout after {elapsed:.1f}s (limit: {fileDownloadTimeout}s)")
        logger.error(f"[TIMEOUT] Endpoint: {endpoint}")
        logger.error(f"[TIMEOUT] URL: {urlForDetails}")
        raise requests.Timeout(
            f'Contact with support support@ivolatility.com\n'
            f'Message for support:\n'
            f'\tWrite your args for endpoint;\n'
            f'\tEndpoint: {endpoint};\n'
            f'\tUrlForDetails: {urlForDetails};'
        )


def setMethod(endpoint):
    loginParams = {}
    if __auth__ is not None:
        pass
    elif __token__ is not None:
        loginParams = {'token': __token__}
    elif __username__ is not None and __password__ is not None:
        loginParams = {'username': __username__, 'password': __password__}

    URL = restApiURL + endpoint
    
    def getMarketDataFromFile(urlForDetails, delayBetweenRequests, fileDownloadTimeout):        
        start = datetime.now()
        logger.info(f"[FILE MODE] Starting async file download mode")
        logger.info(f"[FILE MODE] Details URL: {urlForDetails}")
        logger.info(f"[FILE MODE] Timeout: {fileDownloadTimeout}s, Poll interval: {delayBetweenRequests}s")
        
        isNotComplete = True
        iteration = 0
        while isNotComplete:
            iteration += 1
            elapsed = (datetime.now() - start).total_seconds()
            logger.info(f"[FILE WAIT] Iteration #{iteration}, elapsed: {elapsed:.1f}s")
            
            __raiseFileDownloadTimeout(start, fileDownloadTimeout, endpoint, urlForDetails)
            
            # _session instead of requests, added timeout
            logger.debug(f"[FILE WAIT] Checking file status...")
            response = _session.get(urlForDetails, auth=__auth__, timeout=__requestTimeout__)
            response.raise_for_status()
            
            responseJSON = response.json()
            status = responseJSON[0]['meta']['status']
            logger.info(f"[FILE WAIT] Status: {status}")
            
            isNotComplete = status != 'COMPLETE'
            
            if isNotComplete:
                logger.debug(f"[FILE WAIT] Not ready, sleeping {delayBetweenRequests}s...")
                time.sleep(delayBetweenRequests)
        
        logger.info(f"[FILE WAIT] File is COMPLETE, retrieving download URL...")
        url_retry = 0
        while True:
            __raiseFileDownloadTimeout(start, fileDownloadTimeout, endpoint, urlForDetails)
            
            try:
                if 'urlForDownload' in responseJSON[0]['data'][0]:
                    urlForDownload = responseJSON[0]['data'][0]['urlForDownload']
                    logger.info(f"[FILE WAIT] Download URL obtained: {urlForDownload}")
                else:
                    logger.warning(f"[FILE WAIT] No urlForDownload in response, returning empty DataFrame")
                    return pd.DataFrame()
                break
            except IndexError as e:
                url_retry += 1
                elapsed = (datetime.now() - start).total_seconds()
                logger.warning(f"[FILE WAIT] IndexError on urlForDownload (retry #{url_retry}, elapsed: {elapsed:.1f}s)")
                time.sleep(delayBetweenRequests)
                # _session instead of requests, added timeout
                logger.debug(f"[FILE WAIT] Retrying status check...")
                response = _session.get(urlForDetails, auth=__auth__, timeout=__requestTimeout__)
                response.raise_for_status()
                
                responseJSON = response.json()
        
        # _session instead of requests, use fileDownloadTimeout for large files
        logger.info(f"[FILE DOWNLOAD] Starting download (timeout: {__fileDownloadTimeout__}s)...")
        download_start = datetime.now()
        response = _session.get(urlForDownload, auth=__auth__, timeout=__fileDownloadTimeout__)
        download_elapsed = (datetime.now() - download_start).total_seconds()
        response.raise_for_status()
        
        content_size = len(response.content)
        logger.info(f"[FILE DOWNLOAD] Completed in {download_elapsed:.1f}s, size: {content_size:,} bytes ({content_size/1024/1024:.2f} MB)")
        
        logger.debug(f"[FILE DOWNLOAD] Parsing CSV with gzip compression...")
        df = pd.read_csv(BytesIO(response.content), compression='gzip')
        logger.info(f"[FILE DOWNLOAD] Parsed {len(df):,} rows")
        
        total_elapsed = (datetime.now() - start).total_seconds()
        logger.info(f"[FILE MODE] Total time: {total_elapsed:.1f}s")
        return df
        
    def requestMarketData(params):
        delayBetweenRequests = __delayBetweenRequests__
        fileDownloadTimeout  = __fileDownloadTimeout__
        
        if 'delayBetweenRequests' in params.keys(): 
            delayBetweenRequests = params.pop('delayBetweenRequests')
        if 'fileDownloadTimeout' in params.keys(): 
            fileDownloadTimeout = params.pop('fileDownloadTimeout')
        
        # _session instead of requests, added timeout
        global _request_count
        _request_count += 1
        
        logger.info(f"[REQUEST #{_request_count}] GET {URL}")
        logger.debug(f"[REQUEST #{_request_count}] Params: {params}")
        logger.debug(f"[REQUEST #{_request_count}] Timeout: {__requestTimeout__}s")
        
        request_start = datetime.now()
        response = _session.get(URL, auth=__auth__, params=params, timeout=__requestTimeout__)
        request_elapsed = (datetime.now() - request_start).total_seconds()
        
        logger.info(f"[REQUEST #{_request_count}] Response: {response.status_code} in {request_elapsed:.2f}s")
        response.raise_for_status()
        
        if response.status_code == 204:
            logger.info(f"[REQUEST #{_request_count}] No content (204), returning empty DataFrame")
            return pd.DataFrame()
        
        contentType = response.headers['content-type']
        content_size = len(response.content)
        logger.info(f"[REQUEST #{_request_count}] Content-Type: {contentType}, Size: {content_size:,} bytes")
        
        if contentType == 'text/csv':
            logger.debug(f"[REQUEST #{_request_count}] Parsing CSV...")
            df = pd.read_csv(BytesIO(response.content))
            logger.info(f"[REQUEST #{_request_count}] Parsed {len(df):,} rows")
            return df
        elif contentType == 'application/x-bzip':
            # Fixed bug - was 'zip', should be 'bz2' for bzip format
            logger.debug(f"[REQUEST #{_request_count}] Parsing bzip2 compressed CSV...")
            df = pd.read_csv(BytesIO(response.content), compression='bz2')
            logger.info(f"[REQUEST #{_request_count}] Parsed {len(df):,} rows")
            return df
        elif contentType in ['application/json', 'text/plain;charset=UTF-8']:
        
            logger.debug(f"[REQUEST #{_request_count}] Parsing JSON response...")
            responseJSON = response.json()
            
            if isinstance(responseJSON, list):
                logger.info(f"[REQUEST #{_request_count}] JSON list response with {len(responseJSON)} items")
                return pd.DataFrame(responseJSON)
            else:
                urlForDetails = None
                if 'urlForDetails' in responseJSON['status']:
                    urlForDetails = responseJSON['status']['urlForDetails']
                
                if urlForDetails:
                    logger.info(f"[REQUEST #{_request_count}] Async file mode detected, switching to file download...")
                    return getMarketDataFromFile(urlForDetails, delayBetweenRequests, fileDownloadTimeout)
                else:
                    data = responseJSON.get('data', [])
                    logger.info(f"[REQUEST #{_request_count}] JSON data response with {len(data)} items")
                    return pd.DataFrame(data)
        
        logger.error(f"[REQUEST #{_request_count}] Unsupported content-type: {contentType}")
        logger.error(f"[REQUEST #{_request_count}] Status code: {response.status_code}")
        logger.error(f"[REQUEST #{_request_count}] Response text: {response.text[:500]}")
        
        raise NotImplementedError(
            f'For endpoint {endpoint} not implemented.\n'
            f'Contact with support support@ivolatility.com\n'
            f'Message for support:\n'
            f'\tEndpoint: {endpoint};\n'
            f'\tcontent-type: {contentType};\n'
            f'\tStatus Code: {response.status_code};\n'
            f'\tText: {response.text}'
        )
        return pd.DataFrame()

    def factory(**kwargs):
        params = dict(loginParams, **kwargs)
        if 'from_' in params.keys(): 
            params['from'] = params.pop('from_')
        elif '_from' in params.keys(): 
            params['from'] = params.pop('_from')
        elif '_from_' in params.keys(): 
            params['from'] = params.pop('_from_')
        return requestMarketData(params)

    return factory


# ============================================================
# UTILITY: Get session stats (for debugging)
# ============================================================
def getSessionStats():
    """Get connection pool statistics"""
    stats = {}
    for adapter_prefix, adapter in _session.adapters.items():
        if hasattr(adapter, 'poolmanager') and adapter.poolmanager:
            pools = adapter.poolmanager.pools
            stats[adapter_prefix] = {
                'num_pools': len(pools),
                'pools': {str(k): v.num_connections for k, v in pools.items()} if pools else {}
            }
    return stats
