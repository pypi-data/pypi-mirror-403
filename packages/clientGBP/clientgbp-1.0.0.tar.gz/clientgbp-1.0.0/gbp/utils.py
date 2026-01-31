"""
Utilidades para validación de datos.
"""

import re
from bs4 import BeautifulSoup
from email_validator import validate_email as validate_email_lib, EmailNotValidError
from gbp.models import Client, Contact
from gbp.enums import ClientType


def parse_html(html: str) -> BeautifulSoup:
    """Parsea un string HTML y retorna un objeto BeautifulSoup.

    Args:
        html: String HTML

    Returns:
        BeautifulSoup: Objeto BeautifulSoup parseado
    """
    return BeautifulSoup(html, "html.parser")


def is_valid_cuit(cuit: str) -> bool:
    """Valida si un CUIT es válido.

    Args:
        cuit: CUIT a validar (puede tener o no guiones)

    Returns:
        bool: True si el CUIT es válido, False caso contrario
    """
    cuit_cleaned = re.sub(r"[a-zA-Z]", "", cuit)

    # 2. Intentar extraer el patrón: 2 dígitos + sep(0-5 chars) + 8 dígitos + sep(0-5 chars) + 1 dígito
    # El usuario especifica: XX(5 chars max)8digitos(5 chars max)1digito
    # También debe iniciar con 2 o 3 (prefijos 20, 23, 24, 27, 30, 33, 34...)

    # Regex explicada:
    # ^([23]\d)      : Empieza con 2 o 3 seguido de otro dígito (Grupo 1: prefijo)
    # ([^0-9]{0,5})  : Separador 1: hasta 5 caracteres no numéricos (Grupo 2: ignorar)
    # (\d{8})        : 8 dígitos consecutivos (Grupo 3: documento)
    # ([^0-9]{0,5})  : Separador 2: hasta 5 caracteres no numéricos (Grupo 4: ignorar)
    # (\d{1})$       : Termina con 1 dígito (Grupo 5: verificador)
    match = re.match(r"^([23]\d)([^0-9]{0,5})(\d{8})([^0-9]{0,5})(\d{1})$", cuit_cleaned)

    if not match:
        return False

    cuit = f"{match.group(1)}{match.group(3)}{match.group(5)}"

    if len(cuit) != 11:
        return False

    multiplicadores = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]
    suma = sum(int(cuit[i]) * multiplicadores[i] for i in range(10))
    resto = suma % 11
    digito_verificador = 11 - resto
    if digito_verificador == 11:
        digito_verificador = 0
    if digito_verificador == 10:
        return False
    return int(cuit[10]) == digito_verificador


def is_valid_email(email: str) -> bool:
    """Valida si un email tiene formato válido usando email-validator.

    Args:
        email: Email a validar

    Returns:
        bool: True si el email es válido, False caso contrario
    """
    try:
        validate_email_lib(email, check_deliverability=False)
        return True
    except EmailNotValidError:
        return False


def get_input_value(soup, name: str) -> str:
    """Obtiene el valor de un input o textarea por nombre.

    Args:
        soup: BeautifulSoup object
        name: Nombre del campo

    Returns:
        str: Valor del campo o cadena vacía
    """
    tag = soup.find("input", {"name": name})
    if tag:
        return tag.get("value", "")
    tag = soup.find("textarea", {"name": name})
    if tag:
        return tag.get_text() or ""
    tag = soup.find("select", {"name": name})
    if tag:
        selected = tag.find("option", selected=True)
        return selected.get("value", "") if selected else ""
    return ""


def get_select_value(soup, name: str) -> str:
    """Obtiene el valor seleccionado de un select por nombre.

    Args:
        soup: BeautifulSoup object
        name: Nombre del campo

    Returns:
        str: Valor seleccionado o cadena vacía
    """
    tag = soup.find("select", {"name": name})
    if tag:
        selected = tag.find("option", selected=True)
        if selected:
            return selected.get("value", "")
    return ""


def get_select_text(soup, name: str) -> str:
    """Obtiene el texto de la opción seleccionada de un select por nombre.

    Args:
        soup: BeautifulSoup object
        name: Nombre del campo

    Returns:
        str: Texto de la opción seleccionada o cadena vacía
    """
    tag = soup.find("select", {"name": name})
    if tag:
        selected = tag.find("option", selected=True)
        if selected:
            return selected.get_text() or ""
    return ""


def get_dni(cuit: str) -> str:
    """Obtiene el DNI a partir de un CUIT.

    Args:
        cuit: CUIT (puede tener o no guiones)

    Returns:
        str: DNI extraído del CUIT o cadena vacía si no se encuentra
    """
    # Limpiamos todo excepto números para contar longitud
    cuit_digits = re.sub(r"[^0-9]", "", cuit)

    if len(cuit_digits) == 8:
        return cuit_digits

    cuit_cleaned = re.sub(r"[a-zA-Z]", "", cuit)
    match = re.match(r"^([23]\d)([^0-9]{0,5})(\d{8})([^0-9]{0,5})(\d{1})$", cuit_cleaned)

    if match:
        return match.group(3)

    return ""


def _get_input_val(tag) -> str:
    return tag.get("value", "")


def _get_textarea_val(tag) -> str:
    return tag.get_text() or ""


def _get_select_val(tag) -> str:
    selected = tag.find("option", selected=True)
    if selected:
        return selected.get("value", "")
    return ""


def _get_span_val(tag) -> str:
    return tag.get_text() or ""


_TAG_HANDLERS = {
    "input": _get_input_val,
    "textarea": _get_textarea_val,
    "select": _get_select_val,
    "span": _get_span_val,
}


def get_option_value_by_text(soup, select_id: str, text: str) -> str:
    """Obtiene el value de un option dentro de un select, buscando por su texto.

    Args:
        soup: BeautifulSoup object
        select_id: ID del elemento select
        text: Texto del option a buscar

    Returns:
        str: Value del option o cadena vacía si no se encuentra
    """
    select = soup.find("select", {"id": select_id})
    if not select:
        return ""
    text_normalized = text.strip().lower()
    for option in select.find_all("option"):
        if option.text.strip().lower() == text_normalized:
            return option.get("value", "")
    return ""


def get_seller_number(soup, seller_name: str) -> str:
    """Obtiene el número de vendedor a partir del nombre.

    Args:
        soup: BeautifulSoup object
        seller_name: Nombre del vendedor

    Returns:
        str: Número de vendedor o cadena vacía
    """
    seller_dropdown = "tcPrincipal_tp_0_DDLsm_id"
    return get_option_value_by_text(soup, seller_dropdown, seller_name)


def get_state_number(soup, state_name: str) -> str:
    """Obtiene el número de provincia a partir del nombre.

    Args:
        soup: BeautifulSoup object
        state_name: Nombre de la provincia

    Returns:
        str: Número de provincia o cadena vacía
    """
    state_dropdown = "tcPrincipal_tp_0_DDLstate_id"
    return get_option_value_by_text(soup, state_dropdown, state_name)


def get_value_by_id(soup, element_id: str) -> str:
    """Obtiene el valor de un elemento (input, textarea, select, span) por ID.

    Args:
        soup: BeautifulSoup object
        element_id: ID del elemento

    Returns:
        str: Valor del elemento o cadena vacía
    """
    tag = soup.find(id=element_id)
    if not tag:
        return ""

    handler = _TAG_HANDLERS.get(tag.name)
    if handler:
        return handler(tag)

    return ""


def parse_contact_form(soup) -> Contact | None:
    """Parsea el formulario de edición de contacto y construye un objeto Contact.

    Args:
        soup: BeautifulSoup object del formulario de edición

    Returns:
        Contact | None: Objeto Contact con los datos extraídos
    """
    try:
        return Contact(
            name=get_input_value(soup, "tcPrincipal$tp_0$VCcontact_name"),
            email=get_input_value(soup, "tcPrincipal$tp_0$VCcontact_email"),
            phone=get_input_value(soup, "tcPrincipal$tp_0$VCcontact_phone") or "0",
            tax_number=get_input_value(soup, "tcPrincipal$tp_0$VCcontact_taxNumber"),
            seller_number=get_select_value(soup, "tcPrincipal$tp_0$DDLsm_id"),
            seller_name=get_select_text(soup, "tcPrincipal$tp_0$DDLsm_id"),
            crm=get_input_value(soup, "tcPrincipal$tp_1$ACcust_id$act_txt"),
        )
    except Exception:
        return None


def parse_client_form(soup) -> Client | None:
    """Parsea el formulario de edición de cliente y construye un objeto Client.

    Args:
        soup: BeautifulSoup object del formulario de edición

    Returns:
        Client | None: Objeto Client con los datos extraídos
    """

    try:
        cuit_raw = get_input_value(soup, "tcPrincipal$tp_0$VCcust_taxNumber")

        client_type_id = get_select_value(soup, "tcPrincipal$tp_0$DDLck_id")
        type_client_map = {
            "13": ClientType.CLIENT_C,
            "14": ClientType.END_USER,
        }
        type_client = type_client_map.get(client_type_id, ClientType.CLIENT_C)

        return Client(
            state=get_select_text(soup, "tcPrincipal$tp_0$DDLstate_id"),
            state_number=get_select_value(soup, "tcPrincipal$tp_0$DDLstate_id"),
            tax_number=cuit_raw,
            company_name=get_input_value(soup, "tcPrincipal$tp_0$VCcust_lastName"),
            city=get_input_value(soup, "tcPrincipal$tp_0$ACcity_id$act_txt") or "-",
            address=get_input_value(soup, "tcPrincipal$tp_0$VCcust_address") or "-",
            zip_code=get_input_value(soup, "tcPrincipal$tp_0$VCcust_zip") or "-",
            phone=get_input_value(soup, "tcPrincipal$tp_0$VCcust_phone1") or "0",
            seller_name=get_select_text(soup, "tcPrincipal$tp_0$DDLsm_id"),
            seller_number=get_select_value(soup, "tcPrincipal$tp_0$DDLsm_id"),
            name=get_input_value(soup, "tcPrincipal$tp_0$VCcust_contact"),
            email=get_input_value(soup, "tcPrincipal$tp_0$VCcust_email"),
            type_client=type_client,
        )
    except Exception:
        return None


def extract_all_form_fields(soup: BeautifulSoup) -> dict[str, str]:
    """Extrae todos los campos de un formulario (input, select, textarea).

    Args:
        soup: BeautifulSoup object

    Returns:
        dict: Diccionario con nombre_campo -> valor
    """
    fields = {}

    # Inputs
    for tag in soup.find_all("input", {"name": True}):
        name = tag.get("name")
        if name not in fields:
            fields[name] = tag.get("value", "")

    # Textareas
    for tag in soup.find_all("textarea", {"name": True}):
        name = tag.get("name")
        if name not in fields:
            fields[name] = tag.get_text() or ""

    # Selects
    for tag in soup.find_all("select", {"name": True}):
        name = tag.get("name")
        if name not in fields:
            selected = tag.find("option", selected=True)
            fields[name] = selected.get("value", "") if selected else ""

    return fields
