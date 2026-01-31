"""
ClientGBP: Realiza la sesión con GBP y permite realizar operaciones
"""

import logging
import re
from urllib.parse import urlencode
from bs4 import BeautifulSoup
from requests import HTTPError, RequestException, Response, Session
from requests_toolbelt import MultipartEncoder

from gbp.constants import (
    BASE_HEADERS,
    BASE_URL,
    CONTACT_SEARCH_URL,
    CUSTOMER_WS_URL,
    DEFAULT_TIMEOUT,
    EDIT_URL,
    FILES_UPLOAD,
    HEADERS_AJAX,
    HEADERS_JSON_CONTACT,
    HEADERS_LOGIN,
    HEADERS_UPDATE_BASE,
    LOGIN_URL,
    MAIN_URL,
    SEARCH_URL,
    CONTACT_CREATE_URL,
)
from gbp.models import Client, Contact


from gbp.payloads import (
    create_client_payload,
    create_contact_payload,
    crm_payload,
    login_payload,
    logout_payload,
    search_client_payload,
    search_contact_payload,
    update_client_payload,
    update_contact_payload,
)
from gbp.utils import (
    get_dni,
    get_input_value,
    get_seller_number,
    get_state_number,
    parse_client_form,
    parse_contact_form,
    parse_html,
)

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class ClientGBP:
    """
    Representa la sesión con GBP. Permite loguearse y realizar operaciones con clientes y contactos
    mediante solicituds HTTP simulando el comportamiento del navegador.
    """

    def __init__(self, username: str, password: str) -> None:
        """
        Inicializa la sesión con GBP
        Args:
            username (str): Nombre de usuario
            password (str): Contraseña
        """
        self.username = username
        self.password = password
        self.session = Session()
        self.is_logged_in = False
        self._set_headers()

    def login(self) -> bool:
        """
        Ingresa a la página de GBP y realiza una solicitud HTTP para loguearse y obtener
        el token de sesión.

        Returns:
            bool: True si el login fue exitoso, False en caso contrario
        """
        if self.is_logged_in:
            return True
        logger.info("Redireccionando a la página de login...")
        resp_get = self._navigate_to(LOGIN_URL)

        soup = parse_html(resp_get.text)

        logger.info("Realizando login...")
        resp_post = self._send_post(LOGIN_URL, login_payload(soup, self.username, self.password), HEADERS_LOGIN)

        if self._is_redirect(resp_post.text):
            logger.info("Login exitoso")
            self.is_logged_in = True
            self._set_main_page()
            return True

        logger.error(f"Login fallido. Respuesta: {resp_post.text[:200]}...")
        return False

    def logout(self) -> bool:
        """
        Cierra la sesión de GBP
        Returns:
            bool: True si el logout fue exitoso, False en caso contrario
        """
        if not self.is_logged_in:
            return False

        try:
            soup_header, header_url = self._get_header_page_details()
            if not soup_header or not header_url:
                logger.warning("No se pudo obtener la página de cabecera para logout")
                return False

            logger.info("Cerrando sesión...")
            resp = self._send_post(
                header_url,
                logout_payload(soup_header),
                HEADERS_AJAX,
                allow_redirects=True,
            )

            if self._is_logout(resp.text):
                logger.info("Logout exitoso")
                self.is_logged_in = False
                return True

            logger.error(f"Logout fallido. Respuesta:\n{resp.text}")
            return False
        except RequestException as e:
            logger.error(f"Error durante el logout: {e}")
            return False

    def exists_client_cuit(self, cuit: str) -> bool:
        """Verifica si existe un cliente con el CUIT especificado.

        Args:
            cuit (str): CUIT del cliente (solo números, sin guiones)

        Returns:
            bool: True si existe, False caso contrario
        """
        client = self.get_client_by_dni(cuit)
        return client is not None

    def exists_client_email(self, email: str) -> bool:
        """Verifica si existe un cliente con el email especificado.

        Args:
            email (str): Email del cliente

        Returns:
            bool: True si existe, False caso contrario
        """
        client = self.get_client_by_email(email)
        return client is not None

    def get_client_by_dni(self, cuit: str) -> Client | None:
        """Busca un cliente por CUIT or DNI.

        Args:
            cuit (str): CUIT o DNI del cliente

        Returns:
            Client | None: Objeto Client si se encuentra, None caso contrario
        """
        if not self.is_logged_in:
            logger.warning("Debe estar logueado para buscar clientes")
            return None

        dni = get_dni(cuit)
        try:
            keys = self._get_valid_search_keys()
            if not keys:
                return None
            _, viewstate_key, session_key = keys

            logger.info(f"Buscando cliente con DNI/CUIT: {dni}")

            resp_search = self._send_post(
                SEARCH_URL,
                search_client_payload(viewstate_key, session_key, cuit=dni),
                HEADERS_AJAX,
            )

            if not self._has_results_client(resp_search.text):
                logger.info(f"No se encontraron resultados para CUIT: {dni}")
                return None
            edit_url = self._extract_client_edit_url(resp_search.text)
            if not edit_url:
                logger.warning("No se pudo extraer la URL de edición del cliente")
                return None

            logger.info("Navegando a página de edición del cliente")
            resp_edit = self._navigate_to(edit_url)

            client = parse_client_form(parse_html(resp_edit.text))
            return client

        except RequestException as e:
            logger.error(f"Error durante la búsqueda de cliente: {e}")
            return None

    def search_contact_with_email_cuit(self, email: str, cuit: str) -> Contact | None:
        """
        Busca contactos por email, itera sobre los resultados y verifica si el CUIT
        especificado está en el campo CRM. Retorna el contacto si coincide.

        Args:
            email (str): Email del contacto a buscar
            cuit (str): CUIT a buscar dentro del campo CRM del contacto

        Returns:
            Contact | None: El contacto encontrado o None
        """
        if not self.is_logged_in:
            logger.warning("Debe estar logueado para buscar contactos")
            return None

        try:
            keys = self._get_valid_contact_search_keys()
            if not keys:
                return None
            _, viewstate_key, session_key = keys

            logger.info(f"Buscando contacto por email: {email} para verificar CUIT CRM: {cuit}")

            resp_search = self._send_post(
                CONTACT_SEARCH_URL,
                search_contact_payload(viewstate_key, session_key, email=email),
                HEADERS_AJAX,
            )

            if not self._has_results_client(resp_search.text):
                logger.info(f"No se encontraron resultados para email: {email}")
                return None

            pattern = r"wfmGenericEditNew\.aspx','(\?[^']+)'"
            matches = re.findall(pattern, resp_search.text)

            urls = [f"{BASE_URL}/wfmGenericEditNew.aspx{match}" for match in matches]
            urls = list(dict.fromkeys(urls))

            logger.info(f"Se encontraron {len(urls)} candidatos. Verificando CRM...")

            for url in urls:
                try:
                    resp_edit = self._navigate_to(url)
                    contact = parse_contact_form(parse_html(resp_edit.text))

                    dni = get_dni(cuit)
                    if contact and contact.crm and dni in contact.crm:
                        logger.info(f"Contacto encontrado con CUIT/DNI {cuit}/{dni} en CRM: {contact.name}")
                        return contact
                except Exception as e_inner:
                    logger.error(f"Error al verificar candidato {url}: {e_inner}")
                    continue

            logger.warning(f"No se encontró ningún contacto con CUIT {cuit} en el campo CRM entre los resultados.")
            return None

        except RequestException as e:
            logger.error(f"Error durante la búsqueda extendida de contacto: {e}")
            return None

    def exists_contact_with_email_cuit(self, email: str, cuit: str) -> bool:
        """
        Verifica si existe un contacto con el email y CUIT (en CRM) especificados.

        Args:
            email (str): Email a buscar
            cuit (str): CUIT a buscar en CRM

        Returns:
            bool: True si existe, False caso contrario
        """
        contact = self.search_contact_with_email_cuit(email, cuit)
        return contact is not None

    def get_client_by_email(self, email: str) -> Client | None:
        """Busca un cliente por email.

        Args:
            email (str): Email del cliente

        Returns:
            Client | None: Objeto Client si se encuentra, None caso contrario
        """
        if not self.is_logged_in:
            logger.warning("Debe estar logueado para buscar clientes")
            return None

        try:
            keys = self._get_valid_search_keys()
            if not keys:
                return None
            _, viewstate_key, session_key = keys

            logger.info(f"Buscando cliente con email: {email}")

            resp_search = self._send_post(
                SEARCH_URL,
                search_client_payload(viewstate_key, session_key, email=email),
                HEADERS_AJAX,
            )

            if not self._has_results_client(resp_search.text):
                logger.info(f"No se encontraron resultados para email: {email}")
                return None

            edit_url = self._extract_client_edit_url(resp_search.text)
            if not edit_url:
                logger.warning("No se pudo extraer la URL de edición del cliente")
                return None

            logger.info("Navegando a página de edición del cliente")
            resp_edit = self._navigate_to(edit_url)

            client = parse_client_form(parse_html(resp_edit.text))
            return client

        except RequestException as e:
            logger.error(f"Error durante la búsqueda de cliente: {e}")
            return None

    def get_contact_edit_url_by_email(self, email: str) -> str | None:
        """Obtiene la URL de edición de un contacto por email.

        Args:
            email (str): Email del contacto

        Returns:
            str | None: URL de edición si se encuentra, None caso contrario
        """
        if not self.is_logged_in:
            logger.warning("Debe estar logueado para buscar contactos")
            return None

        try:
            keys = self._get_valid_contact_search_keys()
            if not keys:
                return None
            _, viewstate_key, session_key = keys

            logger.info(f"Buscando contacto con email: {email}")

            resp_search = self._send_post(
                CONTACT_SEARCH_URL,
                search_contact_payload(viewstate_key, session_key, email=email),
                HEADERS_AJAX,
            )

            if not self._has_results_client(resp_search.text):
                logger.info(f"No se encontraron resultados para email: {email}")
                return None

            edit_url = self._extract_client_edit_url(resp_search.text)
            if not edit_url:
                logger.warning("No se pudo extraer la URL de edición del contacto")
                return None

            return edit_url

        except RequestException as e:
            logger.error(f"Error durante la búsqueda de URL de contacto: {e}")
            return None

    def get_contact_by_email(self, email: str) -> Contact | None:
        """Busca un contacto por email.

        Args:
            email (str): Email del contacto

        Returns:
            Contact | None: Objeto Contact si se encuentra, None caso contrario
        """
        edit_url = self.get_contact_edit_url_by_email(email)
        if not edit_url:
            return None

        try:
            logger.info("Navegando a página de edición del contacto")
            resp_edit = self._navigate_to(edit_url)

            contact = parse_contact_form(parse_html(resp_edit.text))
            return contact

        except RequestException as e:
            logger.error(f"Error durante la obtención del contacto: {e}")
            return None

    def exists_contact(self, email: str) -> bool:
        """Verifica si existe un contacto con el email especificado.

        Args:
            email (str): Email del contacto

        Returns:
            bool: True si existe, False caso contrario
        """
        contact = self.get_contact_by_email(email)
        return contact is not None

    def _get_valid_contact_search_keys(self) -> tuple[BeautifulSoup, str, str] | None:
        """
        Obtiene y valida las claves de sesión necesarias para realizar búsquedas de CONTACTOS.
        Returns:
            tuple[BeautifulSoup, str, str] | None: (soup, viewstate_key, session_key) si éxito, None si falla
        """
        return self._get_page_session_keys(CONTACT_SEARCH_URL)

    def create_client(self, client: Client) -> bool:
        """
        Crea un nuevo cliente.
        Args:
            client (Client): Datos del cliente a crear
        Returns:
            bool: True si éxito, False si error
        """
        if not self.is_logged_in:
            logger.warning("Debe estar logueado para crear clientes")
            return False

        try:
            # Obtener claves de sesión de la página de creación de cliente
            logger.info("Navegando a wfmGenericEditNew.aspx...")
            keys = self._get_page_session_keys(EDIT_URL)

            if not keys:
                logger.error("No se pudieron obtener las claves de sesión para crear cliente")
                return False
            soup, viewstate_key_create, session_key_create = keys

            seller_number = get_seller_number(soup, client.seller_name)
            state_number = get_state_number(soup, client.state)

            if not seller_number:
                raise ValueError(f"No se pudo obtener el número de vendedor para el vendedor: {client.seller_name}")
            if not state_number:
                raise ValueError(f"No se pudo obtener el número de estado para el estado: {client.state}")

            client.seller_number = seller_number
            client.state_number = state_number

            payload = create_client_payload(viewstate_key_create, session_key_create, client)
            m = MultipartEncoder(fields=payload)

            self._send_post(EDIT_URL, data=m, headers={"Content-Type": m.content_type})
            resp_create = self._send_post(EDIT_URL, data=payload, files=FILES_UPLOAD)

            if "pageRedirect" in resp_create.text and "Error" in resp_create.text:
                logger.error("Error al crear cliente")
                return False

            return True

        except Exception as e:
            logger.error(f"Error al crear cliente: {e}")
            return False

    def update_client(self, client: Client) -> bool:
        """
        Actualiza los datos de un cliente existente.
        Args:
            client (Client): Datos del cliente a actualizar
        Returns:
            bool: True si éxito, False si error
        """
        if not self.is_logged_in:
            logger.warning("Debe estar logueado para actualizar clientes")
            return False

        try:
            keys = self._get_valid_search_keys()
            if not keys:
                return False
            _, viewstate_key, session_key = keys

            logger.info(f"Buscando cliente para actualizar: {client.tax_number}")

            payload_search = search_client_payload(viewstate_key, session_key, cuit=client.tax_number)
            resp_search = self._send_post(SEARCH_URL, payload_search, HEADERS_AJAX)

            edit_url = self._extract_client_edit_url(resp_search.text)
            if not edit_url:
                logger.error("No se pudo extraer URL de edición")
                return False

            logger.info("Navegando a formulario de edición...")
            keys = self._get_page_session_keys(edit_url)
            if not keys:
                return False
            soup_edit, _, _ = keys

            logger.info(f"Enviando actualización para cliente {client.tax_number}")

            if not self._has_results_client(resp_search.text):
                logger.error(f"No se encontró el cliente {client.tax_number} para actualizar")
                return False

            seller_number = get_seller_number(soup_edit, client.seller_name)
            client.seller_number = seller_number
            payload_update = update_client_payload(soup=soup_edit, client=client)

            resp_update = self._send_post(edit_url, payload_update, HEADERS_UPDATE_BASE)

            if resp_update.status_code == 200 and self._is_redirect(resp_update.text):
                logger.info("Actualización de cliente exitosa")
                return True

            logger.warning(f"Error en actualización cliente. Status: {resp_update.status_code}")
            return False

        except Exception as e:
            logger.error(f"Error al actualizar cliente: {e}")
            return False

    def create_contact(self, contact: Contact) -> bool:
        """
        Crea un nuevo contacto.
        Args:
            contact (Contact): Objeto Contact con los datos a crear
        Returns:
            bool: True si la creación fue exitosa
        """
        if not self.is_logged_in:
            logger.warning("Debe estar logueado para crear contactos")
            return False

        try:
            keys = self._get_page_session_keys(CONTACT_CREATE_URL)
            if not keys:
                logger.error("No se pudieron obtener claves de sesión")
                return False

            soup, viewstate_key, session_key = keys
            seller_number = get_seller_number(soup, contact.seller_name)

            if not viewstate_key or not session_key:
                raise ValueError("No se pudieron obtener claves de sesión para iniciar creación")
            if not seller_number:
                raise ValueError(f"No se pudo obtener el número de vendedor para el vendedor: {contact.seller_name}")

            contact.seller_number = seller_number
            contact.crm = self._get_crm(contact.tax_number)
            logger.info("Iniciando creación de contacto...")

            payload = create_contact_payload(viewstate_key, session_key, contact)
            resp = self._send_post_multipart(CONTACT_CREATE_URL, payload)

            if resp.status_code != 200:
                logger.error(f"Error al crear contacto. Status: {resp.status_code}")
                return False

            return True
        except Exception as e:
            logger.error(f"Error al crear contacto: {e}")
            return False

    def update_contact(self, contact: Contact) -> bool:
        """
        Actualiza los datos de un contacto existente:
        - El vendedor asociado al objeto contact.
        - El campo cuit
        - Si no tiene teléfono, lo coloca en 0.

        Args:
            contact: Objeto Contact con los datos actualizados.

        Returns:
            bool: True si la actualización fue exitosa, False en caso contrario.
        """
        if not self.is_logged_in:
            logger.warning("Debe estar logueado para actualizar contactos")
            return False

        edit_url = self.get_contact_edit_url_by_email(contact.email)
        if not edit_url:
            logger.warning(f"No se encontró el contacto {contact.email} para actualizar")
            return False

        try:
            keys = self._get_page_session_keys(edit_url)
            if not keys:
                return False
            soup, viewstate_key, session_key = keys

            logger.info("Enviando actualización para contacto...")

            seller_number = get_seller_number(soup, contact.seller_name)
            contact.seller_number = seller_number
            payload = update_contact_payload(soup, viewstate_key, session_key, contact)
            resp_update = self._send_post(edit_url, payload, HEADERS_UPDATE_BASE)

            if resp_update.status_code == 200 and self._is_redirect(resp_update.text):
                logger.info("Actualización exitosa (Redirect detectado)")
                return True

            return False
        except Exception as e:
            logger.error(f"Error al actualizar contacto: {e}")
            return False

    def _navigate_to(self, url: str) -> Response:
        """
        Navega a una URL y retorna la respuesta.
        Verifica el estado de la respuesta.
        Args:
            url (str): URL a la que navegar
        Returns:
            Response: Respuesta de la solicitud
        """
        try:
            response = self.session.get(url, timeout=DEFAULT_TIMEOUT)
            response.raise_for_status()
            return response
        except HTTPError as e:
            logger.error("Error al navegar a %s: HTTPError", url, exc_info=e)
            raise
        except RequestException as e:
            logger.error("Error al navegar a %s: RequestException", url, exc_info=e)
            raise

    def _send_post(
        self,
        url: str,
        data: list[tuple[str, str]],
        headers: dict[str, str] | None = None,
        **kwargs,
    ) -> Response:
        """
        Realiza una solicitud POST y retorna la respuesta.
        Args:
            url (str): URL a la que enviar la solicitud
            data (list[tuple[str, str]]): Datos a enviar
            headers (dict[str, str]): Headers de la solicitud
        Returns:
            Response: Respuesta de la solicitud
        """
        try:
            if isinstance(data, (dict, list)) and "files" not in kwargs:
                data = urlencode(data)
            response = self.session.post(url, data=data, headers=headers, timeout=DEFAULT_TIMEOUT, **kwargs)
            return response
        except RequestException as e:
            logger.error("Error al enviar POST a %s: RequestException", url, exc_info=e)
            raise

    def _send_post_json(
        self,
        url: str,
        json_data: dict,
        headers: dict[str, str] | None = None,
    ) -> Response:
        """
        Realiza una solicitud POST con payload JSON y retorna la respuesta.
        Args:
            url (str): URL a la que enviar la solicitud
            json_data (dict): Datos a enviar como JSON
            headers (dict[str, str]): Headers de la solicitud
        Returns:
            Response: Respuesta de la solicitud
        """
        try:
            response = self.session.post(url, json=json_data, headers=headers, timeout=DEFAULT_TIMEOUT)
            return response
        except RequestException as e:
            logger.error("Error al enviar POST JSON a %s: RequestException", url, exc_info=e)
            raise

    def _send_post_multipart(
        self,
        url: str,
        data: list[tuple[str, str]],
        files: dict | None = None,
    ) -> Response:
        """
        Realiza una solicitud POST con multipart/form-data.
        Args:
            url (str): URL a la que enviar la solicitud
            data (list[tuple[str, str]]): Datos a enviar
            files (dict): Archivos a enviar (puede ser {} para forzar multipart)
        Returns:
            Response: Respuesta de la solicitud
        """
        try:
            response = self.session.post(url, data=data, files=files or {}, timeout=DEFAULT_TIMEOUT)
            return response
        except RequestException as e:
            logger.error("Error al enviar POST multipart a %s: RequestException", url, exc_info=e)
            raise

    def _get_page_session_keys(self, url: str) -> tuple[BeautifulSoup, str, str] | None:
        """
        Navega a una URL y extrae las claves de sesión (viewstate_key, session_key).

        Args:
            url (str): URL de la página a navegar

        Returns:
            tuple[BeautifulSoup, str, str] | None: (soup, viewstate_key, session_key) si éxito, None si falla
        """
        try:
            resp = self._navigate_to(url)
            soup = parse_html(resp.text)

            viewstate_key = get_input_value(soup, "__VIEWSTATE_KEY")
            session_key = get_input_value(soup, "__SESSION_KEY")

            if not viewstate_key or not session_key:
                logger.error(f"No se pudieron obtener las claves de sesión de: {url}")
                return None

            return soup, viewstate_key, session_key
        except RequestException as e:
            logger.error(f"Error al obtener página {url}: %s", exc_info=e)
            return None

    def _get_valid_search_keys(self) -> tuple[BeautifulSoup, str, str] | None:
        """
        Obtiene y valida las claves de sesión necesarias para realizar búsquedas de CLIENTES.

        Returns:
            tuple[BeautifulSoup, str, str] | None: (soup, viewstate_key, session_key) si éxito, None si falla
        """
        return self._get_page_session_keys(SEARCH_URL)

    def _has_results_client(self, html: str) -> bool:
        """
        Verifica si la búsqueda arrojó resultados.
        Args:
            html (str): HTML de la página de resultados
        Returns:
            bool: True si hay resultados, False caso contrario
        """
        return "grdData" in html

    def _extract_client_edit_url(self, html: str) -> str | None:
        """
        Extrae la URL de edición de un cliente desde los resultados de búsqueda.

        Args:
            html (str): HTML de la página de resultados

        Returns:
            str | None: URL completa de edición o None si no se encuentra
        """
        pattern = r"wfmGenericEditNew\.aspx','(\?[^']+)'"
        matches = re.findall(pattern, html)
        if matches:
            edit_key = matches[0]
            return f"{BASE_URL}/wfmGenericEditNew.aspx{edit_key}"
        return None

    def _get_header_page_details(self) -> tuple[BeautifulSoup | None, str | None]:
        """
        Obtiene los detalles de la página de cabecera perteneciente a la página principal.

        Returns:
            tuple: (soup, header_url)
        """
        try:
            resp_main = self._navigate_to(MAIN_URL)

            soup_main = parse_html(resp_main.text)
            frame_header = soup_main.find("frame", {"id": "frameHeader"})
            header_src = frame_header.get("src") if frame_header else "wfmHeader.aspx"

            header_url = f"{BASE_URL}/{header_src}"
            resp_header = self._navigate_to(header_url)

            return parse_html(resp_header.text), header_url

        except RequestException as e:
            logger.error("Error al cargar la página principal o cabecera: %s", exc_info=e)
            return None, None

    def _get_crm(self, cuit: str) -> str | None:
        """
        Busca un cliente en el CRM por CUIT para asociarlo a un contacto.
        Llama al webservice customerGetText.

        Args:
            cuit (str): CUIT del cliente a buscar

        Returns:
            str | None: String con el formato "Nombre Cliente (ID)" si se encuentra, None si no.
                        Ejemplo: "GLOBAL BLUE POINT S.A. (50031)"
        """

        if not self.is_logged_in:
            logger.warning("Debe estar logueado para buscar contactos")
            return None

        try:
            resp_customer = self._send_post_json(CUSTOMER_WS_URL, crm_payload(cuit), HEADERS_JSON_CONTACT)
            logger.debug(resp_customer.text)
            if resp_customer.status_code != 200:
                logger.error(f"Error en búsqueda CRM. Status: {resp_customer.status_code}")
                return None

            # Obtiene los resultados encontrados y lo parsea a JSON para manejarlo de mejor manera.
            customer_data = resp_customer.json()
            clients_crm = customer_data["d"]
            total_clients = len(clients_crm)
            if total_clients == 0:
                logger.warning("No se encontró cliente con ese CUIT")
                return None

            if total_clients > 1:
                dolar_crm_client = [client for client in clients_crm if "PESOS" not in client]
                return dolar_crm_client[0]

            return customer_data["d"][0]
        except Exception as e:
            logger.error(f"Error inesperado buscando en CRM: {e}")
            return None

    def _set_main_page(self) -> None:
        """
        Setea la carga de la página principal.
        Se realiza de esta manera para la redirección.

        Args:
            None
        Returns:
            None
        """
        self._get_header_page_details()

    def _set_headers(self) -> None:
        """
        Setea los headers de la sesión
        Args:
            None
        Returns:
            None
        """
        self.session.headers.update(BASE_HEADERS)

    def _is_redirect(self, text: str) -> bool:
        """
        Verifica si la respuesta indica una redirección (éxito en operación).
        Args:
            text (str): Texto de la respuesta
        Returns:
            bool: True si hay redirección
        """
        return "pageRedirect" in text

    def _is_logout(self, text: str) -> bool:
        """
        Verifica si la respuesta indica que se cerró la sesión.
        Args:
            text (str): Texto de la respuesta
        Returns:
            bool: True si se cerró la sesión
        """
        return "parent.closeIFrame();" in text

    def __str__(self) -> str:
        return f"ClientGBP(username={self.username}, password={self.password}, is_logged_in={self.is_logged_in})"
