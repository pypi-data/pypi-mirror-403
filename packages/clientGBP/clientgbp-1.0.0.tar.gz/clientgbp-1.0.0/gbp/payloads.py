"""
Payloads para el cliente de GBP.

"""

from bs4 import BeautifulSoup

from gbp.utils import get_dni, get_input_value
from gbp.enums import ClientType
from gbp.models import Client, Contact

# El ordén de los campos en cada payload debe ser exactamente igual del que se consume desde el navegador, cualquier cambio de ordén romperia la solicitud HTPP.


def login_payload(soup: BeautifulSoup, username: str, password: str) -> list[tuple[str, str]]:
    """Obtener payload para el login.

    Args:
        soup: BeautifulSoup object
        username: Nombre de usuario
        password: Contraseña

    Returns:
        Payload para el login
    """
    viewstate = _get_input_value(soup, "__VIEWSTATE")
    viewstate_gen = _get_input_value(soup, "__VIEWSTATEGENERATOR")
    return [
        ("ScriptManager1", "updPanFilters|wucIB_Login$LB"),
        ("UserName", username),
        ("Password", password),
        ("wucIB_Login$hidDisableAfterClick", "0"),
        ("inputHidden", "N"),
        ("inputUser", ""),
        ("hidMsg1", "El Serial ingresado no se encuentra cargado."),
        ("hidMsg2", "Está seguro que desea borrar el serial:"),
        ("hidOk", "Ok"),
        ("hidCancel", "Cancelar"),
        ("hidP2DC", _get_input_value(soup, "hidP2DC") or "Dvhvru4"),
        ("WucMsgBox1$wucMB_me", ""),
        ("WucMsgBox1$wucMB_btnOk$hidDisableAfterClick", "0"),
        ("WucMsgBox1$wucMB_btnCancel$hidDisableAfterClick", "0"),
        ("WucMsgBox1$wucMB_btnRetry$hidDisableAfterClick", "0"),
        ("__EVENTTARGET", "wucIB_Login$LB"),
        ("__EVENTARGUMENT", ""),
        ("__VIEWSTATE", viewstate),
        ("__VIEWSTATEGENERATOR", viewstate_gen),
        ("__ASYNCPOST", "true"),
        ("", ""),
    ]


def search_client_payload(viewstate_key: str, session_key: str, cuit: str = "", email: str = "") -> list[tuple[str, str]]:
    """Obtener payload para la búsqueda de clientes (por CUIT o Email).

    Args:
        viewstate_key: Valor de __VIEWSTATE_KEY de la página de búsqueda
        session_key: Valor de __SESSION_KEY de la página de búsqueda
        cuit: CUIT del cliente a buscar (opcional)
        email: Email del cliente a buscar (opcional)

    Returns:
        Payload para la búsqueda de clientes
    """

    ddl_tax_number = "1" if cuit else "-1"
    ddl_email = "1" if email else "-1"

    # Si se pasa CUIT, extraer el DNI porque el buscador espera el DNI en TBcust_taxNumber
    if cuit:
        cuit = get_dni(cuit)

    return [
        ("ScriptManager1", "updPanFilters|wucIB_Search$LB"),
        ("__SESSION_KEY", session_key),
        ("__VIEWSTATE", ""),
        ("wucCBSuggest$wucCB2_cpe_ClientState", "true"),
        ("wucCB$wucCB_cpe_ClientState", "false"),
        ("wucIB_ClearFilters2$hidDisableAfterClick", "0"),
        ("wucIB_Search2$hidDisableAfterClick", "0"),
        ("DDLcust_id", "-1"),
        ("TBcust_idFrom", "0"),
        ("TBcust_idFrom_ViewState", "Value|=0|=PromptChar|=_%20|=ShowNullText|=true|=NullText|=%20|=Increment|=1"),
        ("TBcust_idTo", "0"),
        ("TBcust_idTo_ViewState", "Value|=0|=PromptChar|=_%20|=ShowNullText|=true|=NullText|=%20|=Increment|=1"),
        ("DDLcurr_id", "-1"),
        ("DDLcountry_id", "-1"),
        ("DDLstate_id", "-1"),
        ("DDLfc_id", "-1"),
        ("DDLtnt_id", "-1"),
        ("DDLcust_taxNumber", ddl_tax_number),
        ("TBcust_taxNumber", cuit),
        ("DDLcust_lastName", "-1"),
        ("TBcust_lastName", ""),
        ("DDLcust_firstname", "-1"),
        ("TBcust_firstname", ""),
        ("DDLcust_name1", "-1"),
        ("TBcust_name1", ""),
        ("DDLcity_id", "-1"),
        ("TBcity_id", ""),
        ("DDLcust_address", "-1"),
        ("TBcust_address", ""),
        ("DDLcust_zip", "-1"),
        ("TBcust_zip", ""),
        ("DDLcust_phone1", "-1"),
        ("TBcust_phone1", ""),
        ("DDLcust_cellPhone2", "-1"),
        ("TBcust_cellPhone2", ""),
        ("DDLcust_whatsapp", "-1"),
        ("TBcust_whatsapp", ""),
        ("DDLcust_cellPhone", "-1"),
        ("TBcust_cellPhone", ""),
        ("DDLact_id", "-1"),
        ("DDLsm_id", "-1"),
        ("DDLss_id", "-1"),
        ("DDLck_id", "-1"),
        ("DDLdl_id", "-1"),
        ("DDLcust_contact", "-1"),
        ("TBcust_contact", ""),
        ("DDLcust_email", ddl_email),
        ("TBcust_email", email),
        ("DDLcust_migrationID", "-1"),
        ("TBcust_migrationID", ""),
        ("DDLcust_address4Delivery", "-1"),
        ("TBcust_address4Delivery", ""),
        ("DDLcust_address4Payments", "-1"),
        ("TBcust_address4Payments", ""),
        ("DDLcust_phone2", "-1"),
        ("TBcust_phone2", ""),
        ("DDLcust_cellPhone2_notes", "-1"),
        ("TBcust_cellPhone2_notes", ""),
        ("DDLcust_cellPhone1_notes", "-1"),
        ("TBcust_cellPhone1_notes", ""),
        ("DDLst_id", "-1"),
        ("DDLdisc_id", "-1"),
        ("DDLprli_id", "-1"),
        ("DDLcust_credit_max", "-1"),
        ("TBcust_credit_maxFrom", "0.00"),
        ("TBcust_credit_maxFrom_ViewState", "Value|=0.00|=PromptChar|=_%20|=ShowNullText|=true|=NullText|=%20|=Increment|=1"),
        ("TBcust_credit_maxTo", "0.00"),
        ("TBcust_credit_maxTo_ViewState", "Value|=0.00|=PromptChar|=_%20|=ShowNullText|=true|=NullText|=%20|=Increment|=1"),
        ("DDLcust_credit_own", "-1"),
        ("TBcust_credit_ownFrom", "0.00"),
        ("TBcust_credit_ownFrom_ViewState", "Value|=0.00|=PromptChar|=_%20|=ShowNullText|=true|=NullText|=%20|=Increment|=1"),
        ("TBcust_credit_ownTo", "0.00"),
        ("TBcust_credit_ownTo_ViewState", "Value|=0.00|=PromptChar|=_%20|=ShowNullText|=true|=NullText|=%20|=Increment|=1"),
        ("DDLcust_credit_Curr_Id", "-1"),
        ("DDLcust_credit_max_overComeDate", "-1"),
        ("TBcust_credit_max_overComeDateFrom", ""),
        ("MEEcust_credit_max_overComeDateFrom_ClientState", ""),
        ("TBcust_credit_max_overComeDateTo", ""),
        ("MEEcust_credit_max_overComeDateTo_ClientState", ""),
        ("DDLcust_credit_max_Last", "-1"),
        ("TBcust_credit_max_LastFrom", "0.00"),
        ("TBcust_credit_max_LastFrom_ViewState", "Value|=0.00|=PromptChar|=_%20|=ShowNullText|=true|=NullText|=%20|=Increment|=1"),
        ("TBcust_credit_max_LastTo", "0.00"),
        ("TBcust_credit_max_LastTo_ViewState", "Value|=0.00|=PromptChar|=_%20|=ShowNullText|=true|=NullText|=%20|=Increment|=1"),
        ("DDLcust_SaleOrderMaxValue", "-1"),
        ("TBcust_SaleOrderMaxValueFrom", "0.00"),
        ("TBcust_SaleOrderMaxValueFrom_ViewState", "Value|=0.00|=PromptChar|=_%20|=ShowNullText|=true|=NullText|=%20|=Increment|=1"),
        ("TBcust_SaleOrderMaxValueTo", "0.00"),
        ("TBcust_SaleOrderMaxValueTo_ViewState", "Value|=0.00|=PromptChar|=_%20|=ShowNullText|=true|=NullText|=%20|=Increment|=1"),
        ("ctl92", "-1"),
        ("ctl94", "-1"),
        ("ctl96", "-1"),
        ("ctl98", "-1"),
        ("DDLstor_id", "-1"),
        ("DDLbra_id", "-1"),
        ("DDLbrag_id", "-1"),
        ("DDLrmap_id", "-1"),
        ("DDLprli_id_alternative", "-1"),
        ("DDLprli_id_alternative_upTo", "-1"),
        ("TBprli_id_alternative_upToFrom", ""),
        ("MEEprli_id_alternative_upToFrom_ClientState", ""),
        ("TBprli_id_alternative_upToTo", ""),
        ("MEEprli_id_alternative_upToTo_ClientState", ""),
        ("DDLsm_id_2", "-1"),
        ("ctl112", "-1"),
        ("DDLcust_birthDay", "-1"),
        ("TBcust_birthDayFrom", ""),
        ("MEEcust_birthDayFrom_ClientState", ""),
        ("TBcust_birthDayTo", ""),
        ("MEEcust_birthDayTo_ClientState", ""),
        ("DDLcust_age", "-1"),
        ("TBcust_ageFrom", "0"),
        ("TBcust_ageFrom_ViewState", "Value|=0|=PromptChar|=_%20|=ShowNullText|=true|=NullText|=%20|=Increment|=1"),
        ("TBcust_ageTo", "0"),
        ("TBcust_ageTo_ViewState", "Value|=0|=PromptChar|=_%20|=ShowNullText|=true|=NullText|=%20|=Increment|=1"),
        ("DDLrating_id", "-1"),
        ("DDLcust_maleOrFemale", "-1"),
        ("DDLmarst_id", "-1"),
        ("ctl125", "-1"),
        ("DDLcust_ownerOf", "-1"),
        ("TBcust_ownerOf", ""),
        ("DDLcust_remuneration", "-1"),
        ("TBcust_remunerationFrom", "0.00"),
        ("TBcust_remunerationFrom_ViewState", "Value|=0.00|=PromptChar|=_%20|=ShowNullText|=true|=NullText|=%20|=Increment|=1"),
        ("TBcust_remunerationTo", "0.00"),
        ("TBcust_remunerationTo_ViewState", "Value|=0.00|=PromptChar|=_%20|=ShowNullText|=true|=NullText|=%20|=Increment|=1"),
        ("DDLcram_id", "-1"),
        ("DDLcust_ramification", "-1"),
        ("TBcust_ramification", ""),
        ("DDLcust_jobTitle", "-1"),
        ("TBcust_jobTitle", ""),
        ("DDLcust_jobAddress", "-1"),
        ("TBcust_jobAddress", ""),
        ("DDLcust_jobPhone", "-1"),
        ("TBcust_jobPhone", ""),
        ("DDLcust_jobName", "-1"),
        ("TBcust_jobName", ""),
        ("DDLcust_jobPayDate", "-1"),
        ("TBcust_jobPayDateFrom", ""),
        ("MEEcust_jobPayDateFrom_ClientState", ""),
        ("TBcust_jobPayDateTo", ""),
        ("MEEcust_jobPayDateTo_ClientState", ""),
        ("DDLcust_jobAdmissionDate", "-1"),
        ("TBcust_jobAdmissionDateFrom", ""),
        ("MEEcust_jobAdmissionDateFrom_ClientState", ""),
        ("TBcust_jobAdmissionDateTo", ""),
        ("MEEcust_jobAdmissionDateTo_ClientState", ""),
        ("DDLcust_jobYearInIt", "-1"),
        ("TBcust_jobYearInItFrom", "0"),
        ("TBcust_jobYearInItFrom_ViewState", "Value|=0|=PromptChar|=_%20|=ShowNullText|=true|=NullText|=%20|=Increment|=1"),
        ("TBcust_jobYearInItTo", "0"),
        ("TBcust_jobYearInItTo_ViewState", "Value|=0|=PromptChar|=_%20|=ShowNullText|=true|=NullText|=%20|=Increment|=1"),
        ("ctl156", "-1"),
        ("DDLcorp_id", "-1"),
        ("DDLdef_id", "-1"),
        ("ctl160", "-1"),
        ("ctl163", "-1"),
        ("DDLstcIB_Id", "-1"),
        ("DDLcust_taxIBNumber", "-1"),
        ("TBcust_taxIBNumber", ""),
        ("DDLacc_count_id", "-1"),
        ("TBacc_count_id", ""),
        ("ctl170", "-1"),
        ("DDLcust_ElectronicInvoice_MiPyme_Mode", "-1"),
        ("DDLcust_contact4Payments", "-1"),
        ("TBcust_contact4Payments", ""),
        ("DDLcust_email4Payments", "-1"),
        ("TBcust_email4Payments", ""),
        ("DDLcust_contact4Management", "-1"),
        ("TBcust_contact4Management", ""),
        ("DDLcust_email4Management", "-1"),
        ("TBcust_email4Management", ""),
        ("DDLcust_contact4Administration", "-1"),
        ("TBcust_contact4Administration", ""),
        ("DDLcust_email4Administration", "-1"),
        ("TBcust_email4Administration", ""),
        ("DDLcust_contact4Logistics", "-1"),
        ("TBcust_contact4Logistics", ""),
        ("DDLcust_email4Logistics", "-1"),
        ("TBcust_email4Logistics", ""),
        ("DDLcust_contact4Alternative", "-1"),
        ("TBcust_contact4Alternative", ""),
        ("DDLcust_email4Alternative", "-1"),
        ("TBcust_email4Alternative", ""),
        ("DDLcust_contact4AlternativeII", "-1"),
        ("TBcust_contact4AlternativeII", ""),
        ("DDLcust_email4AlternativeII", "-1"),
        ("TBcust_email4AlternativeII", ""),
        ("DDLcust_contact4RMA", "-1"),
        ("TBcust_contact4RMA", ""),
        ("DDLcust_email4RMA", "-1"),
        ("TBcust_email4RMA", ""),
        ("DDLcust_address4RMA", "-1"),
        ("TBcust_address4RMA", ""),
        ("DDLcust_phone4RMA", "-1"),
        ("TBcust_phone4RMA", ""),
        ("DDLcust_cd", "-1"),
        ("TBcust_cdFrom", ""),
        ("MEEcust_cdFrom_ClientState", ""),
        ("TBcust_cdTo", ""),
        ("MEEcust_cdTo_ClientState", ""),
        ("DDLcust_partnerOf", "-1"),
        ("TBcust_partnerOf", ""),
        ("DDLcust_web", "-1"),
        ("TBcust_web", ""),
        ("DDLcust_annotation", "-1"),
        ("TBcust_annotation", ""),
        ("DDLcust_fax", "-1"),
        ("TBcust_fax", ""),
        ("DDLcoslis_id", "-1"),
        ("DDLcoslis_idB", "-1"),
        ("ctl224", "-1"),
        ("DDLcust_webNickName", "-1"),
        ("TBcust_webNickName", ""),
        ("DDLstg_id", "-1"),
        ("DDLcust_MercadoLibreNickName", "-1"),
        ("TBcust_MercadoLibreNickName", ""),
        ("ctl231", "-1"),
        ("ctl234", "-1"),
        ("ctl236", "-1"),
        ("DDLcust_note1", "-1"),
        ("TBcust_note1", ""),
        ("DDLcust_note2", "-1"),
        ("TBcust_note2", ""),
        ("DDLcust_note3", "-1"),
        ("TBcust_note3", ""),
        ("DDLcust_note4", "-1"),
        ("TBcust_note4", ""),
        ("DDLcust_notes", "-1"),
        ("TBcust_notes", ""),
        ("ctl251", "-1"),
        ("DDLcust_CRMComment", "-1"),
        ("TBcust_CRMComment", ""),
        ("ctl257", "-1"),
        ("DDLuser_id4Insert", "-1"),
        ("DDLuser_id4LastUpdate", "-1"),
        ("DDLcust_LastUpdate", "-1"),
        ("TBcust_LastUpdateFrom", ""),
        ("MEEcust_LastUpdateFrom_ClientState", ""),
        ("TBcust_LastUpdateTo", ""),
        ("MEEcust_LastUpdateTo_ClientState", ""),
        ("wucIB_ClearFilters$hidDisableAfterClick", "0"),
        ("wucIB_Search$hidDisableAfterClick", "0"),
        ("wucIB_Insert$hidDisableAfterClick", "0"),
        ("wucRefreshGrid$hidDisableAfterClick", "0"),
        ("wucIB_ViewAllFields$hidDisableAfterClick", "0"),
        ("wucIB_50$hidDisableAfterClick", "0"),
        ("wucIB_maxRows$hidDisableAfterClick", "0"),
        ("grdData$ctl18$txtPageNumber", ""),
        ("grdData$ctl18$btnSearchPage11$hidDisableAfterClick", "0"),
        ("hidHeader", ""),
        ("hidTooltipUpdate", "Modificar Registro"),
        ("hidTooltipDelete", "Eliminar Registro"),
        ("hidTooltipColumnOrderUp", "Ordenar Columna Ascendente"),
        ("hidTooltipColumnOrderDown", "Ordenar Columna Descendete"),
        ("hidTooltipColumnOrderNot", "Quitar Orden de Columna"),
        ("hidTooltipThumbnail", "Click sobre la imagen para agrandar"),
        ("hidSignal", ""),
        ("hidTooltipColumn3", ""),
        ("hidTooltipColumn4", ""),
        ("hidMsg1", "E R R O R"),
        ("hidMsg2", "No se obtuvieron datos para mostrar de la tabla requerida."),
        ("hidMsg3", "Ubicación geográfica"),
        ("wucMB$wucMB_me", ""),
        ("wucMB$wucMB_btnOk$hidDisableAfterClick", "0"),
        ("wucMB$wucMB_btnCancel$hidDisableAfterClick", "0"),
        ("wucMB$wucMB_btnRetry$hidDisableAfterClick", "0"),
        ("wucEB4CustomQueryByPage$hidControlType", "1"),
        ("wucEB4CustomQueryByPage$hidID", "-1"),
        ("wucEB4CustomQueryByPage$hidUnderControlByProfile", "False"),
        ("wucEB4CustomQueryByPage$hidReloadOpenerPage", "False"),
        ("wucEB4CustomQueryByPage$hidVSFromEasyButton", "*"),
        ("wucEB4CustomQueryByPage$hidGUID", ""),
        ("wucEB4ProcedureManual$hidControlType", "1"),
        ("wucEB4ProcedureManual$hidID", "-1"),
        ("wucEB4ProcedureManual$hidUnderControlByProfile", "False"),
        ("wucEB4ProcedureManual$hidReloadOpenerPage", "False"),
        ("wucEB4ProcedureManual$hidVSFromEasyButton", "*"),
        ("wucEB4ProcedureManual$hidGUID", ""),
        ("__EVENTTARGET", "wucIB_Search$LB"),
        ("__EVENTARGUMENT", ""),
        ("__LASTFOCUS", ""),
        ("__VIEWSTATE_KEY", viewstate_key),
        ("__AjaxControlToolkitCalendarCssLoaded", ""),
        ("__ASYNCPOST", "true"),
        ("", ""),
    ]


def logout_payload(soup: BeautifulSoup) -> list[tuple[str, str]]:
    """Obtener payload para el logout.

    Args:
        soup: BeautifulSoup object

    Returns:
        Payload para el logout
    """
    viewstate = _get_input_value(soup, "__VIEWSTATE")
    viewstate_gen = _get_input_value(soup, "__VIEWSTATEGENERATOR")
    event_validation = _get_input_value(soup, "__EVENTVALIDATION")
    return [
        ("ctl00$ScriptManager1", "ctl00$UpdatePanel1|lnkLogout"),
        ("__EVENTTARGET", "lnkLogout"),
        ("__EVENTARGUMENT", ""),
        ("__VIEWSTATE", viewstate),
        ("__VIEWSTATEGENERATOR", viewstate_gen),
        ("__EVENTVALIDATION", event_validation),
        ("__ASYNCPOST", "true"),
    ]


def _get_input_value(soup: BeautifulSoup, name: str) -> str:
    """Obtener valor de un input por nombre.

    Args:
        soup: BeautifulSoup object
        name: Nombre del input

    Returns:
        Valor del input
    """
    tag = soup.find("input", {"name": name})
    return tag.get("value", "") if tag else ""


def search_contact_payload(viewstate_key: str, session_key: str, email: str = "") -> list[tuple[str, str]]:
    """Obtener payload para la búsqueda de contactos por Email.

    Args:
        viewstate_key: Valor de __VIEWSTATE_KEY
        session_key: Valor de __SESSION_KEY
        email: Email del contacto a buscar

    Returns:
        Payload para la búsqueda de contactos
    """
    ddl_email = "1" if email else "-1"

    return [
        ("ScriptManager1", "updPanFilters|wucIB_Search$LB"),
        ("__EVENTTARGET", "wucIB_Search$LB"),
        ("__EVENTARGUMENT", ""),
        ("__LASTFOCUS", ""),
        ("__VIEWSTATE_KEY", viewstate_key),
        ("__SESSION_KEY", session_key),
        ("__VIEWSTATE", ""),
        ("wucCB$wucCB_cpe_ClientState", "false"),
        ("wucIB_ClearFilters2$hidDisableAfterClick", "0"),
        ("wucIB_Search2$hidDisableAfterClick", "0"),
        ("DDLcontact_id", "-1"),
        ("TBcontact_idFrom", "0"),
        ("TBcontact_idFrom_ViewState", "Value|=0|=PromptChar|=_%20|=ShowNullText|=true|=NullText|=%20|=Increment|=1"),
        ("TBcontact_idTo", "0"),
        ("TBcontact_idTo_ViewState", "Value|=0|=PromptChar|=_%20|=ShowNullText|=true|=NullText|=%20|=Increment|=1"),
        ("DDLbra_id", "-1"),
        ("DDLcontact_name", "-1"),
        ("TBcontact_name", ""),
        ("DDLcontact_desc", "-1"),
        ("TBcontact_desc", ""),
        ("DDLcontact_address", "-1"),
        ("TBcontact_address", ""),
        ("DDLcontact_zip", "-1"),
        ("TBcontact_zip", ""),
        ("DDLcountry_id", "-1"),
        ("DDLstate_id", "-1"),
        ("DDLcity_id", "-1"),
        ("TBcity_id", ""),
        ("DDLcontact_phone", "-1"),
        ("TBcontact_phone", ""),
        ("DDLcontact_email", ddl_email),
        ("TBcontact_email", email),
        ("DDLcontact_BirthDate", "-1"),
        ("TBcontact_BirthDateFrom", ""),
        ("MEEcontact_BirthDateFrom_ClientState", ""),
        ("TBcontact_BirthDateTo", ""),
        ("MEEcontact_BirthDateTo_ClientState", ""),
        ("DDLsm_id", "-1"),
        ("DDLfc_id", "-1"),
        ("DDLtnt_id", "-1"),
        ("DDLcontact_taxNumber", "-1"),
        ("TBcontact_taxNumber", ""),
        ("DDLconclass_id", "-1"),
        ("DDLcust_id", "-1"),
        ("TBcust_id", ""),
        ("DDLuser_id4Insert", "-1"),
        ("DDLuser_id4LastUpdate", "-1"),
        ("DDLuser_LastUpdate", "-1"),
        ("TBuser_LastUpdateFrom", ""),
        ("MEEuser_LastUpdateFrom_ClientState", ""),
        ("TBuser_LastUpdateTo", ""),
        ("MEEuser_LastUpdateTo_ClientState", ""),
        ("wucIB_ClearFilters$hidDisableAfterClick", "0"),
        ("wucIB_Search$hidDisableAfterClick", "0"),
        ("wucIB_Insert$hidDisableAfterClick", "0"),
        ("wucRefreshGrid$hidDisableAfterClick", "0"),
        ("wucIB_ViewAllFields$hidDisableAfterClick", "0"),
        ("wucIB_50$hidDisableAfterClick", "0"),
        ("wucIB_maxRows$hidDisableAfterClick", "0"),
        ("grdData$ctl18$txtPageNumber", ""),
        ("grdData$ctl18$btnSearchPage11$hidDisableAfterClick", "0"),
        ("hidHeader", ""),
        ("hidTooltipUpdate", "Modificar Registro"),
        ("hidTooltipDelete", "Eliminar Registro"),
        ("hidTooltipColumnOrderUp", "Ordenar Columna Ascendente"),
        ("hidTooltipColumnOrderDown", "Ordenar Columna Descendete"),
        ("hidTooltipColumnOrderNot", "Quitar Orden de Columna"),
        ("hidTooltipThumbnail", "Click sobre la imagen para agrandar"),
        ("hidSignal", ""),
        ("hidTooltipColumn3", ""),
        ("hidTooltipColumn4", ""),
        ("hidMsg1", "E R R O R"),
        ("hidMsg2", "No se obtuvieron datos para mostrar de la tabla requerida."),
        ("hidMsg3", "Ubicación geográfica"),
        ("wucMB$wucMB_me", ""),
        ("wucMB$wucMB_btnOk$hidDisableAfterClick", "0"),
        ("wucMB$wucMB_btnCancel$hidDisableAfterClick", "0"),
        ("wucMB$wucMB_btnRetry$hidDisableAfterClick", "0"),
        ("wucEB4CustomQueryByPage$hidControlType", "1"),
        ("wucEB4CustomQueryByPage$hidID", "-1"),
        ("wucEB4CustomQueryByPage$hidUnderControlByProfile", "False"),
        ("wucEB4CustomQueryByPage$hidReloadOpenerPage", "False"),
        ("wucEB4CustomQueryByPage$hidVSFromEasyButton", "*"),
        ("wucEB4CustomQueryByPage$hidGUID", ""),
        ("wucEB4ProcedureManual$hidControlType", "1"),
        ("wucEB4ProcedureManual$hidID", "-1"),
        ("wucEB4ProcedureManual$hidUnderControlByProfile", "False"),
        ("wucEB4ProcedureManual$hidReloadOpenerPage", "False"),
        ("wucEB4ProcedureManual$hidVSFromEasyButton", "*"),
        ("wucEB4ProcedureManual$hidGUID", ""),
        ("__ASYNCPOST", "true"),
        ("", ""),
    ]


def update_contact_payload(soup: BeautifulSoup, viewstate_key: str, session_key: str, contact: Contact) -> list[tuple[str, str]]:
    """
    Genera el payload mínimo para actualizar un contacto.

    Args:
        soup: BeautifulSoup object del formulario de edición del contacto
        viewstate_key: Key del viewstate
        session_key: Key de la sesión
        contact: Contacto con los datos a actualizar

    Returns:
        list[tuple[str, str]]: Payload completo para la actualización
    """
    tc_state = get_input_value(soup, "tcPrincipal_ClientState")

    phone_value = contact.phone if contact.phone else (get_input_value(soup, "tcPrincipal$tp_0$VCcontact_phone") or "0")
    tax_value = contact.tax_number if contact.tax_number else get_input_value(soup, "tcPrincipal$tp_0$VCcontact_taxNumber") or ""
    crm_value = contact.crm if contact.crm else get_input_value(soup, "tcPrincipal$tp_1$ACcust_id$act_txt") or ""
    name_value = contact.name if contact.name else get_input_value(soup, "tcPrincipal$tp_0$VCcontact_name") or ""

    return [
        # 1. __LASTFOCUS primero (Patrón observado en update_client_payload)
        ("__LASTFOCUS", ""),
        ("__EVENTTARGET", "btnOk$LB"),
        ("__EVENTARGUMENT", ""),
        # Campos de sesión
        ("tcPrincipal_ClientState", tc_state),  # '{"ActiveTabIndex":0,"TabState":[true,true,true]}'
        ("__VIEWSTATE_KEY", viewstate_key),
        ("__SESSION_KEY", session_key),
        ("__VIEWSTATE", ""),
        # 2. Campos a modificar (Tab 0)
        ("tcPrincipal$tp_0$DDLbra_id", "-1"),
        ("tcPrincipal$tp_0$VCcontact_name", name_value),
        ("tcPrincipal$tp_0$VCcontact_phone", phone_value),
        ("tcPrincipal$tp_0$MEEDAcontact_BirthDate_ClientState", ""),
        ("tcPrincipal$tp_0$DDLsm_id", contact.seller_number),
        ("tcPrincipal$tp_0$VCcontact_taxNumber", tax_value),
        # Tab 1 - CRM
        ("tcPrincipal$tp_1$ACcust_id$act_txt", crm_value),
        ("tcPrincipal$tp_1$ACcust_id$act_tbwe_ClientState", ""),
        ("tcPrincipal$tp_1$ACcust_id$Hidden1", ""),
        ("tcPrincipal$tp_1$ACcust_id$hidBehaviorId", "ACcust_id_behavior"),
        ("tcPrincipal$tp_1$ACcust_id$hidSelectedID", ""),
        # 3. Botones al final
        ("btnOk$hidDisableAfterClick", "0"),
        ("btnExit$hidDisableAfterClick", "0"),
    ]


def crm_payload(cuit: str) -> dict[str, str | int]:
    """Obtener payload para la búsqueda del CRM completo de un cliente para crear un contacto.

    Args:
        cuit: CUIT del cliente a buscar

    Returns:
        Payload para la búsqueda en CRM (formato JSON)
    """
    dni = get_dni(cuit)
    return {
        "prefixText": dni,
        "count": 20,
        "contextKey": "2/1/1/50031/1/-1/-1/2/-1",
    }


def create_contact_payload(
    viewstate_key: str,
    session_key: str,
    contact: Contact,
):
    """
    Obtener payload para la creación de un contacto.
    """
    return [
        ("tcPrincipal_ClientState", '{"ActiveTabIndex":0,"TabState":[true,true,true]}'),
        ("__EVENTTARGET", "btnOk$LB"),
        ("__EVENTARGUMENT", ""),
        ("__LASTFOCUS", ""),
        ("__VIEWSTATE_KEY", viewstate_key),
        ("__SESSION_KEY", session_key),
        ("__VIEWSTATE", ""),
        ("tcPrincipal$tp_0$DDLbra_id", "-1"),
        ("tcPrincipal$tp_0$VCcontact_name", contact.name),
        ("tcPrincipal$tp_0$VCcontact_desc", ""),
        ("tcPrincipal$tp_0$VCcontact_address", ""),
        ("tcPrincipal$tp_0$VCcontact_zip", ""),
        ("tcPrincipal$tp_0$DDLcountry_id", "54"),
        ("tcPrincipal$tp_0$DDLstate_id", "54020"),
        ("tcPrincipal$tp_0$ACcity_id$act_txt", ""),
        ("tcPrincipal$tp_0$ACcity_id$act_tbwe_ClientState", ""),
        ("tcPrincipal$tp_0$ACcity_id$Hidden1", ""),
        ("tcPrincipal$tp_0$ACcity_id$hidBehaviorId", "ACcity_id_behavior"),
        ("tcPrincipal$tp_0$ACcity_id$hidSelectedID", ""),
        ("tcPrincipal$tp_0$VCcontact_phone", "0"),
        ("tcPrincipal$tp_0$VCcontact_email", contact.email),
        ("tcPrincipal$tp_0$DAcontact_BirthDate", ""),
        ("tcPrincipal$tp_0$MEEDAcontact_BirthDate_ClientState", ""),
        ("tcPrincipal$tp_0$DDLsm_id", contact.seller_number),
        ("tcPrincipal$tp_0$DDLfc_id", "1"),
        ("tcPrincipal$tp_0$DDLtnt_id", "1"),
        ("tcPrincipal$tp_0$VCcontact_taxNumber", contact.tax_number),
        ("tcPrincipal$tp_0$DDLconclass_id", "-1"),
        ("tcPrincipal$tp_1$ACcust_id$act_txt", contact.crm),
        ("tcPrincipal$tp_1$ACcust_id$act_tbwe_ClientState", ""),
        ("tcPrincipal$tp_1$ACcust_id$Hidden1", ""),
        ("tcPrincipal$tp_1$ACcust_id$hidBehaviorId", "ACcust_id_behavior"),
        ("tcPrincipal$tp_1$ACcust_id$hidSelectedID", contact.crm),
        ("tcPrincipal_tp_2_DTuser_LastUpdateTime", "00:00:00"),
        (
            "tcPrincipal_tp_2_DTuser_LastUpdateTime_ViewState",
            "Date|=1,1,1,0,0,0,0|=PromptChar|=_%20|=SmartInputMode|=false|=StartYear|=1950|=ShowNullText|=false|=NullText|=%20",
        ),
        ("tcPrincipal$tp_2$MEEDTuser_LastUpdateDate_ClientState", ""),
        ("btnOk$hidDisableAfterClick", "0"),
        ("btnExit$hidDisableAfterClick", "0"),
        ("wucMB$wucMB_me", ""),
        ("wucMB$wucMB_btnOk$hidDisableAfterClick", "0"),
        ("wucMB$wucMB_btnCancel$hidDisableAfterClick", "0"),
        ("wucMB$wucMB_btnRetry$hidDisableAfterClick", "0"),
        ("hidLblInsert", "Agregar+Registro"),
        ("hidLblUpdate", "Modificar+Registro"),
        ("hidLblDelete", "Eliminar+Registro"),
        ("hidCalendar", "Abrir+calendario"),
        ("hidTimeNow", "Aplicar+Hora+Actual"),
        ("hidDateTimeNow", "Aplicar+Fecha+y+Hora+Actual"),
        ("hidWucMB_Ok", "Aceptar"),
        ("hidWucMB_Cancel", "Cancelar"),
        ("hidWucMB_Message", "Confirma+que+va+a+eliminar+el+registro+seleccionado?"),
        ("hidWucCFUErrorSize", "La+imagen+es+demasiado+grande,+no+debe+superar+los"),
        ("hidMsg1", "ATENCIÓN:+Modo+de+Carga+Secuencial+Activa"),
        ("hidMsg2", "Ingrese+texto+a+buscar+/+**+Código+/+++Parciales"),
        ("hidMsg4", "El+texto+seleccionado+en+<b>#</b>+no+figura+en+la+Base+de+Datos"),
        ("hidReturnValue", ""),
        ("hidCodeEditor1", ""),
        ("wucEB4CustomQueryByPage$hidControlType", "1"),
        ("wucEB4CustomQueryByPage$hidID", "-1"),
        ("wucEB4CustomQueryByPage$hidUnderControlByProfile", "False"),
        ("wucEB4CustomQueryByPage$hidReloadOpenerPage", "False"),
        ("wucEB4CustomQueryByPage$hidVSFromEasyButton", "*"),
        ("wucEB4CustomQueryByPage$hidGUID", ""),
        ("wucEB4ProcedureManual$hidControlType", "1"),
        ("wucEB4ProcedureManual$hidID", "-1"),
        ("wucEB4ProcedureManual$hidUnderControlByProfile", "False"),
        ("wucEB4ProcedureManual$hidReloadOpenerPage", "False"),
        ("wucEB4ProcedureManual$hidVSFromEasyButton", "*"),
        ("wucEB4ProcedureManual$hidGUID", ""),
        ("hiddenInputToUpdateATBuffer_CommonToolkitScripts", "0"),
    ]


def create_client_payload(
    viewstate_key: str,
    session_key: str,
    client: Client,
) -> list[tuple[str, str | tuple]]:
    """
    Obtener payload para la creación de un cliente con el orden EXACTO requerido por el servidor.

    Args:
        viewstate_key: str
        session_key: str
        client: Client
    Returns:
        list[tuple[str, str | tuple]]: Payload para la creación de un cliente con el orden EXACTO requerido por el servidor.
    """
    data_for_type = _get_data_for_type(client)
    return [
        ("__LASTFOCUS", ""),
        ("__EVENTTARGET", "btnOk$LB"),
        ("__EVENTARGUMENT", ""),
        (
            "tcPrincipal_ClientState",
            '{"ActiveTabIndex":0,"TabState":[true,true,true,true,true,true,true,true,true,true,true,true,true,true,true,true,true,true]}',
        ),
        ("__VIEWSTATE_KEY", viewstate_key),
        ("__SESSION_KEY", session_key),
        ("__VIEWSTATE", ""),
        # Tab 0 - Datos principales
        ("tcPrincipal$tp_0$DDLcurr_id", "2"),
        ("tcPrincipal$tp_0$DDLcountry_id", "54"),
        ("tcPrincipal$tp_0$DDLstate_id", "54001"),
        ("tcPrincipal$tp_0$DDLfc_id", "1"),
        ("tcPrincipal$tp_0$DDLtnt_id", "1"),
        ("tcPrincipal$tp_0$VCcust_taxNumber", client.tax_number),
        ("tcPrincipal$tp_0$VCcust_lastName", client.company_name),
        ("tcPrincipal$tp_0$VCcust_firstname", ""),
        ("tcPrincipal$tp_0$VCcust_name1", ""),
        ("tcPrincipal$tp_0$ACcity_id$act_txt", client.city),
        ("tcPrincipal$tp_0$ACcity_id$act_tbwe_ClientState", ""),
        ("tcPrincipal$tp_0$ACcity_id$Hidden1", ""),
        ("tcPrincipal$tp_0$ACcity_id$hidBehaviorId", "ACcity_id_behavior"),
        ("tcPrincipal$tp_0$ACcity_id$hidSelectedID", ""),
        ("tcPrincipal$tp_0$VCcust_address", client.address),
        ("tcPrincipal$tp_0$VCcust_zip", client.zip_code),
        ("tcPrincipal$tp_0$VCcust_phone1", client.phone),
        ("tcPrincipal$tp_0$VCcust_cellPhone2", ""),
        ("tcPrincipal$tp_0$VCcust_whatsapp", ""),
        ("tcPrincipal$tp_0$VCcust_cellPhone", ""),
        ("tcPrincipal$tp_0$DDLact_id", data_for_type["activity"]),
        ("tcPrincipal$tp_0$DDLsm_id", client.seller_number),
        ("tcPrincipal$tp_0$DDLss_id", "-1"),
        ("tcPrincipal$tp_0$DDLck_id", data_for_type["client_type"]),
        ("tcPrincipal$tp_0$DDLdl_id", "1"),
        ("tcPrincipal$tp_0$VCcust_contact", client.name),
        ("tcPrincipal$tp_0$VCcust_email", client.email),
        # Tab 1
        ("tcPrincipal$tp_1$VCcust_address4Delivery", ""),
        ("tcPrincipal$tp_1$VCcust_address4Payments", ""),
        ("tcPrincipal$tp_1$VCcust_phone2", ""),
        ("tcPrincipal$tp_1$VCcust_cellPhone2_notes", ""),
        ("tcPrincipal$tp_1$VCcust_cellPhone1_notes", ""),
        # Tab 2
        ("tcPrincipal$tp_2$DDLst_id", "20"),
        ("tcPrincipal$tp_2$DDLdisc_id", "1"),
        ("tcPrincipal$tp_2$DDLprli_id", data_for_type["price_list"]),
        ("tcPrincipal_tp_2_DEcust_credit_max", "0.00"),
        (
            "tcPrincipal_tp_2_DEcust_credit_max_ViewState",
            "Value|=0.00|=PromptChar|=_%20|=ShowNullText|=false|=NullText|=%20|=Increment|=1",
        ),
        ("tcPrincipal_tp_2_DEcust_credit_own", "0.00"),
        (
            "tcPrincipal_tp_2_DEcust_credit_own_ViewState",
            "Value|=0.00|=PromptChar|=_%20|=ShowNullText|=false|=NullText|=%20|=Increment|=1",
        ),
        ("tcPrincipal$tp_2$DAcust_credit_max_overComeDate", ""),
        ("tcPrincipal$tp_2$MEEDAcust_credit_max_overComeDate_ClientState", ""),
        ("tcPrincipal$tp_2$DDLcust_credit_Curr_Id", "-1"),
        ("tcPrincipal_tp_2_DEcust_credit_max_Last", "0.00"),
        (
            "tcPrincipal_tp_2_DEcust_credit_max_Last_ViewState",
            "Value|=0.00|=PromptChar|=_%20|=ShowNullText|=false|=NullText|=%20|=Increment|=1",
        ),
        ("tcPrincipal_tp_2_DEcust_SaleOrderMaxValue", "0.00"),
        (
            "tcPrincipal_tp_2_DEcust_SaleOrderMaxValue_ViewState",
            "Value|=0.00|=PromptChar|=_%20|=ShowNullText|=false|=NullText|=%20|=Increment|=1",
        ),
        ("tcPrincipal$tp_2$DDLstor_id", "-1"),
        ("tcPrincipal$tp_2$DDLbra_id", "-1"),
        ("tcPrincipal$tp_2$DDLbrag_id", "-1"),
        ("tcPrincipal$tp_2$DDLrmap_id", "1"),
        ("tcPrincipal$tp_2$DDLprli_id_alternative", "-1"),
        ("tcPrincipal$tp_2$DAprli_id_alternative_upTo", ""),
        ("tcPrincipal$tp_2$MEEDAprli_id_alternative_upTo_ClientState", ""),
        ("tcPrincipal$tp_2$DDLsm_id_2", "-1"),
        # Tab 3
        ("tcPrincipal$tp_3$DAcust_birthDay", ""),
        ("tcPrincipal$tp_3$MEEDAcust_birthDay_ClientState", ""),
        ("tcPrincipal_tp_3_INcust_age_ViewState", "Value|=0|=PromptChar|=_%20|=ShowNullText|=true|=NullText|=%20|=Increment|=1"),
        ("tcPrincipal$tp_3$DDLcust_maleOrFemale", "1"),
        ("tcPrincipal$tp_3$DDLmarst_id", "-1"),
        (
            "tcPrincipal_tp_3_DEcust_remuneration_ViewState",
            "Value|=0.00|=PromptChar|=_%20|=ShowNullText|=false|=NullText|=%20|=Increment|=1",
        ),
        ("tcPrincipal$tp_3$ACcust_jobCity_Id$act_tbwe_ClientState", ""),
        ("tcPrincipal$tp_3$ACcust_jobCity_Id$Hidden1", ""),
        ("tcPrincipal$tp_3$ACcust_jobCity_Id$hidBehaviorId", "ACcust_jobCity_Id_behavior"),
        ("tcPrincipal$tp_3$ACcust_jobCity_Id$hidSelectedID", ""),
        ("tcPrincipal$tp_3$MEEDAcust_jobPayDate_ClientState", ""),
        ("tcPrincipal$tp_3$MEEDAcust_jobAdmissionDate_ClientState", ""),
        (
            "tcPrincipal_tp_3_INcust_jobYearInIt_ViewState",
            "Value|=0|=PromptChar|=_%20|=ShowNullText|=true|=NullText|=%20|=Increment|=1",
        ),
        ("tcPrincipal$tp_3$DDLcust_4OnlySign", "1"),
        # Tab 4
        ("tcPrincipal$tp_4$DDLstcIB_Id", "1"),
        ("tcPrincipal$tp_4$VCcust_taxIBNumber", client.tax_number),
        ("tcPrincipal$tp_4$ACacc_count_id$act_txt", ""),
        ("tcPrincipal$tp_4$ACacc_count_id$act_tbwe_ClientState", ""),
        ("tcPrincipal$tp_4$ACacc_count_id$Hidden1", ""),
        ("tcPrincipal$tp_4$ACacc_count_id$hidBehaviorId", "ACacc_count_id_behavior"),
        ("tcPrincipal$tp_4$ACacc_count_id$hidSelectedID", ""),
        ("tcPrincipal$tp_4$DDLsts_sujID", "-1"),
        # Tab 5
        ("tcPrincipal$tp_5$VCcust_contact4Payments", ""),
        ("tcPrincipal$tp_5$VCcust_email4Payments", ""),
        ("tcPrincipal$tp_5$VCcust_contact4Management", ""),
        ("tcPrincipal$tp_5$VCcust_email4Management", ""),
        ("tcPrincipal$tp_5$VCcust_contact4Administration", ""),
        ("tcPrincipal$tp_5$VCcust_email4Administration", ""),
        ("tcPrincipal$tp_5$VCcust_contact4Logistics", ""),
        ("tcPrincipal$tp_5$VCcust_email4Logistics", ""),
        ("tcPrincipal$tp_5$VCcust_contact4Alternative", ""),
        ("tcPrincipal$tp_5$VCcust_email4Alternative", ""),
        ("tcPrincipal$tp_5$VCcust_contact4AlternativeII", ""),
        ("tcPrincipal$tp_5$VCcust_email4AlternativeII", ""),
        ("tcPrincipal$tp_5$VCcust_contact4RMA", ""),
        ("tcPrincipal$tp_5$VCcust_email4RMA", ""),
        ("tcPrincipal$tp_5$VCcust_address4RMA", ""),
        ("tcPrincipal$tp_5$VCcust_phone4RMA", ""),
        # Tab 6
        ("tcPrincipal$tp_6$DAcust_cd", ""),
        ("tcPrincipal$tp_6$MEEDAcust_cd_ClientState", ""),
        ("tcPrincipal$tp_6$VCcust_partnerOf", ""),
        ("tcPrincipal$tp_6$VCcust_web", ""),
        ("tcPrincipal$tp_6$VCcust_annotation", ""),
        ("tcPrincipal$tp_6$VCcust_fax", ""),
        # Tab 7
        ("tcPrincipal$tp_7$DDLcoslis_id", "-1"),
        ("tcPrincipal$tp_7$DDLcoslis_idB", "-1"),
        # Tab 8
        ("tcPrincipal$tp_8$VCcust_webNickName", ""),
        ("tcPrincipal$tp_8$PWcust_webPassword", ""),
        ("tcPrincipal$tp_8$DDLstg_id", "-1"),
        ("tcPrincipal$tp_8$VCcust_MercadoLibreNickName", ""),
        # Tab 9 - FileUpload (AQUÍ en el orden correcto)
        ("tcPrincipal$tp_9$WUCLIcust_picture$FileUpload", ("", b"", "application/octet-stream")),
        # Tab 10
        ("tcPrincipal$tp_10$VCcust_note1", ""),
        ("tcPrincipal$tp_10$VCcust_note2", ""),
        ("tcPrincipal$tp_10$VCcust_note3", ""),
        ("tcPrincipal$tp_10$VCcust_note4", ""),
        # Tab 11
        ("tcPrincipal$tp_11$ACcust_id_related$act_txt", ""),
        ("tcPrincipal$tp_11$ACcust_id_related$act_tbwe_ClientState", ""),
        ("tcPrincipal$tp_11$ACcust_id_related$Hidden1", ""),
        ("tcPrincipal$tp_11$ACcust_id_related$hidBehaviorId", "ACcust_id_related_behavior"),
        ("tcPrincipal$tp_11$ACcust_id_related$hidSelectedID", ""),
        # Tab 12
        ("tcPrincipal$tp_12$VCcust_notes", ""),
        # Tab 14
        ("tcPrincipal$tp_14$VCcust_CRMComment", ""),
        # Tab 16
        ("tcPrincipal$tp_16$VCcol_TCR_1", ""),
        ("tcPrincipal$tp_16$CHcol_GTA_1", ""),
        # Tab 17
        ("tcPrincipal_tp_17_DTcust_LastUpdateTime", "00:00:00"),
        (
            "tcPrincipal_tp_17_DTcust_LastUpdateTime_ViewState",
            "Date|=1,1,1,0,0,0,0|=PromptChar|=_%20|=SmartInputMode|=false|=StartYear|=1950|=ShowNullText|=false|=NullText|=%20",
        ),
        ("tcPrincipal$tp_17$MEEDTcust_LastUpdateDate_ClientState", ""),
        # Botones
        ("btnOk$hidDisableAfterClick", "0"),
        ("btnExit$hidDisableAfterClick", "0"),
        ("wucMB$wucMB_me", ""),
        ("wucMB$wucMB_btnOk$hidDisableAfterClick", "0"),
        ("wucMB$wucMB_btnCancel$hidDisableAfterClick", "0"),
        ("wucMB$wucMB_btnRetry$hidDisableAfterClick", "0"),
        # Labels
        ("hidLblInsert", "Agregar Registro"),
        ("hidLblUpdate", "Modificar Registro"),
        ("hidLblDelete", "Eliminar Registro"),
        ("hidCalendar", "Abrir calendario"),
        ("hidTimeNow", "Aplicar Hora Actual"),
        ("hidDateTimeNow", "Aplicar Fecha y Hora Actual"),
        ("hidWucMB_Ok", "Aceptar"),
        ("hidWucMB_Cancel", "Cancelar"),
        ("hidWucMB_Message", "Confirma que va a eliminar el registro seleccionado?"),
        ("hidWucCFUErrorSize", "La imagen es demasiado grande, no debe superar los"),
        ("hidMsg1", "ATENCIÓN: Modo de Carga Secuencial Activa"),
        ("hidMsg2", "Ingrese texto a buscar / ** Código / + Parciales"),
        ("hidMsg4", "El texto seleccionado en <b>#</b> no figura en la Base de Datos"),
        ("hidReturnValue", ""),
        ("hidCodeEditor1", ""),
        # Easy buttons
        ("wucEB4CustomQueryByPage$hidControlType", "1"),
        ("wucEB4CustomQueryByPage$hidID", "-1"),
        ("wucEB4CustomQueryByPage$hidUnderControlByProfile", "False"),
        ("wucEB4CustomQueryByPage$hidReloadOpenerPage", "False"),
        ("wucEB4CustomQueryByPage$hidVSFromEasyButton", "*"),
        ("wucEB4CustomQueryByPage$hidGUID", ""),
        ("wucEB4ProcedureManual$hidControlType", "1"),
        ("wucEB4ProcedureManual$hidID", "-1"),
        ("wucEB4ProcedureManual$hidUnderControlByProfile", "False"),
        ("wucEB4ProcedureManual$hidReloadOpenerPage", "False"),
        ("wucEB4ProcedureManual$hidVSFromEasyButton", "*"),
        ("wucEB4ProcedureManual$hidGUID", ""),
        ("hiddenInputToUpdateATBuffer_CommonToolkitScripts", "1"),
    ]


def _get_data_for_type(client: Client) -> dict:
    """
    Retorna los values para la actividad, tipo de cliente y lista de precios.

    Args:
        client (Client): El cliente.

    Returns:
        dict: Un diccionario con los values para la actividad, tipo de cliente y lista de precios.
    """
    data = {
        ClientType.CLIENT_C: {"activity": "2", "client_type": "1", "price_list": "7"},
        ClientType.CLIENT_A: {"activity": "2", "client_type": "1", "price_list": "5"},
        ClientType.END_USER: {"activity": "4", "client_type": "14", "price_list": "8"},
    }
    return data.get(client.type_client)


def update_client_payload(
    soup: BeautifulSoup,
    client: Client,
) -> list[tuple[str, str]]:
    """
    Genera el payload mínimo para actualizar un cliente.

    Orden requerido por el servidor:
        1. __LASTFOCUS primero
        2. Campos de sesión y formulario
        3. Campos a modificar
        4. Botones al final

    Args:
        soup: BeautifulSoup object del formulario de edición del cliente
        client: Cliente con los datos a actualizar

    Returns:
        list[tuple[str, str]]: Payload mínimo para la actualización

    Campos que se modifican:
        - DDLprli_id: lista de precios según tipo
        - VCcust_taxIBNumber: DNI extraído del CUIT
        - DDLact_id: actividad según tipo de cliente
        - DDLck_id: tipo de cliente según tipo
        - DDLsm_id: ID del vendedor
        - VCcust_contact: nombre de contacto (firstname o email local)
        - VCcust_firstname: se vacía (el valor se mueve a contact)
        - VCcust_web: siempre vacío
        - VCcust_phone1: "0" si está vacío
    """
    # Extraer claves de sesión
    vs_key = get_input_value(soup, "__VIEWSTATE_KEY")
    session_key = get_input_value(soup, "__SESSION_KEY")
    tc_state = get_input_value(soup, "tcPrincipal_ClientState")

    # Obtener datos según el tipo de cliente
    type_data = {
        ClientType.CLIENT_C: {"activity": "2", "client_type": "1", "price_list": "7"},
        ClientType.CLIENT_A: {"activity": "2", "client_type": "1", "price_list": "5"},
        ClientType.END_USER: {"activity": "4", "client_type": "14", "price_list": "8"},
    }.get(client.type_client, {"activity": "4", "client_type": "14", "price_list": "8"})

    # Lógica para contact: si hay firstname lo usamos, si no hay contact usamos email
    contact_key = "tcPrincipal$tp_0$VCcust_contact"
    firstname_key = "tcPrincipal$tp_0$VCcust_firstname"
    email_key = "tcPrincipal$tp_0$VCcust_email"

    current_contact = (get_input_value(soup, contact_key) or "").strip()
    current_firstname = (get_input_value(soup, firstname_key) or "").strip()
    current_email = (get_input_value(soup, email_key) or "").strip()

    if current_firstname:
        contact_value = current_firstname
    elif current_contact:
        contact_value = current_contact
    else:
        contact_value = current_email.split("@")[0] if current_email else "-"
        contact_value = contact_value if contact_value else "-"

    # Lógica para phone: si está vacío ponerlo en "0"
    current_phone = (get_input_value(soup, "tcPrincipal$tp_0$VCcust_phone1") or "").strip()
    phone_value = current_phone if current_phone else "0"

    # Construir payload con orden correcto
    return [
        # 1. __LASTFOCUS primero
        ("__LASTFOCUS", ""),
        ("__EVENTTARGET", "btnOk$LB"),
        ("__EVENTARGUMENT", ""),
        ("tcPrincipal_ClientState", tc_state),
        ("__VIEWSTATE_KEY", vs_key),
        ("__SESSION_KEY", session_key),
        ("__VIEWSTATE", ""),
        # 2. Campos a modificar
        ("tcPrincipal$tp_0$DDLact_id", type_data["activity"]),
        ("tcPrincipal$tp_0$DDLck_id", type_data["client_type"]),
        ("tcPrincipal$tp_0$DDLsm_id", client.seller_number),
        ("tcPrincipal$tp_0$VCcust_contact", contact_value),
        ("tcPrincipal$tp_0$VCcust_firstname", ""),
        ("tcPrincipal$tp_0$VCcust_phone1", phone_value),
        ("tcPrincipal$tp_2$DDLprli_id", type_data["price_list"]),
        ("tcPrincipal$tp_4$VCcust_taxIBNumber", client.tax_number),
        ("tcPrincipal$tp_6$VCcust_web", ""),
        # 3. Botones al final
        ("btnOk$hidDisableAfterClick", "0"),
        ("btnExit$hidDisableAfterClick", "0"),
    ]
