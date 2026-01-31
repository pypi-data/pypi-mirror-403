"""
Constantes de URLS de GBP.
"""

BASE_URL = "http://gbp83.globalbluepoint.com/techmind"
ORIGIN_URL = "http://gbp83.globalbluepoint.com"
LOGIN_URL = f"{BASE_URL}/wfmLogin.aspx"
MAIN_URL = f"{BASE_URL}/wfmMain.aspx"
HEADER_URL = f"{BASE_URL}/wfmHeader.aspx"
EDIT_URL = f"{BASE_URL}/wfmGenericEditNew.aspx?cQ2v22GXfQfTORj3bhweXzBaCTC/DfFjrH02fBOnH3IfuiXaJv23tyc6vDlGXiCBKkq5e7isquikk0gT4lekmzJfJ9o7Ykxk1LhoSMHKru/6INPb+BEmltnOpjXNBiBB+Y7/dTxjYSdGNUAWL1HDte64yl+HNJnqE+5JJ63+yWOxDFp24Sdtja93Jtk77c5YyjkcZl9+zbF5Gy9yoOKwNZY4SvhG79QKTe3Fb3HRnyc2dce91mT1djmXNfkGPbzx"
SEARCH_URL = f"{BASE_URL}/wfmGeneric.aspx?lExZ2R6/P+z3/C3FRi2g5upIiT8HqZ+2OGFp4BKgOYrOmZumAsw/SsLwPxJMw4M4qHpNpMVWXNPYhd+aVTlOUN4qBAE3eav+H3wBNDHrzHr/yOrQd1uebajx4bx3SlFJSoD16RF61947EW0tYNayRU/XhWTYjGsNZWFJGE8V2WK9eLB7FmkMt23gRohtN0B39B//8g4Q0lqHQpKhwjhScGXFB6CkyPSpv0at2lnoNzhe6N2Tb9Epo+8t9HTIIV33kxKrKLBB+DQStQ8gt7OaPZdKVTmOHfRKX2zVs08dDz19uEs5u1iehXNuvMWkLxrjBF0sM0gVzOj1WzmYocAXG/CSWLFU1bE3fded5ee0lG4aMGKjumP/QsFZTeT1SfZa5ofIggLiRHwoiH1t4Mg2tUbBoV8xvLc4lL1uuOJs037HECbxYYab1yuVbH8GdAEgigVyq90bXLXUw7j5nUTEVmkgWYZ28A8GHnbO21jBTMkfEtTszC8S8IabqSz51If56gMeUnFKA2IwRuhRGwJ3823Tlw6tYzYL8N7aBJfN2LEG7+qGblKbQ/jWpzQbl2WI"
CONTACT_SEARCH_URL = f"{BASE_URL}/wfmGeneric.aspx?1bbJ7bsDV7KkDoMilnqDmbJSEyKtaY3skwDTPGV53J0i9wV3a5zKFbMmLKgk7ErONzzRBQR+mO/qZ6tS+HZPpkxgktqDrW0QrhUaLshzsq0="
CONTACT_CREATE_URL = f"{BASE_URL}/wfmGenericEditNew.aspx?JxogQvq2z8n0ol2qp06V4hAgZaMvd4G0kPZprF2te1ACKZdA4pQDSuj7zrZIVgspzx2mo6Xapi0zVwTlQaktmwHsyl1IQ9RYtGxpiUO9rKF/enGqV/ebXTQc4EAKKaWXyxmc8bUnMggR9If7c+LgZbGf9P97PBRX9oSRc6Osg+h/hchr5VPnH9KbHCs9LF2jzrFB6a1+13ro1HWUUFYTvc2Hs5ywI3Drzer9qHu7JK1zvIjqdHNVlNercKoP1bVZ&_GBPp_*ex=1769605664333"
CUSTOMER_WS_URL = f"{BASE_URL}/App_WebServices/ws_generic.asmx/customerGetText"

DEFAULT_TIMEOUT = 30

BASE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
}

HEADERS_AJAX = {
    "X-MicrosoftAjax": "Delta=true",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Origin": ORIGIN_URL,
    "Cache-Control": "no-cache",
}

HEADERS_LOGIN = {
    **HEADERS_AJAX,
    "Referer": LOGIN_URL,
    "Origin": ORIGIN_URL,
}

HEADERS_JSON_CONTACT = {"Content-Type": "application/json; charset=utf-8", "Accept": "*/*", "Referer": CUSTOMER_WS_URL}

HEADERS_UPDATE_BASE = {
    "Content-Type": "application/x-www-form-urlencoded",
    "Origin": ORIGIN_URL,
}

# FileUpload vacío requerido para el formulario de creación de cliente
FILES_UPLOAD = {
    "tcPrincipal$tp_9$WUCLIcust_picture$FileUpload": ("", "", "application/octet-stream"),
}
