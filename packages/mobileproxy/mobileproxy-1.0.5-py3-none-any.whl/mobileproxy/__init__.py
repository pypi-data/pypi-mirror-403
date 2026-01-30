from typing import Any, Dict, Optional, Sequence, Union

import requests  # type: ignore

ProxyIdLike = Union[int, Sequence[int], str]


class MobileProxy:
    def __init__(self, api_key: Optional[str] = None):
        self.url = "https://mobileproxy.space/api.html"
        self.api_key = api_key

        self.session = requests.Session()
        self.session.headers = {"Authorization": f"Bearer {self.api_key}"}

    def _normalize_id_list(self, value: Optional[ProxyIdLike]) -> Optional[str]:
        if value is None:
            return None
        if isinstance(value, str):
            return value
        if isinstance(value, int):
            return str(value)
        return ",".join(str(item) for item in value)

    def _clean_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return {key: value for key, value in params.items() if value is not None}

    def request(
        self,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        method: str = "GET",
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Make a request to the MobileProxy API.

        :param params: Query parameters to send with the request.
        :param data: Data to send with the request.
        :param method: HTTP method to use for the request. Default is "GET".
        :return: The response from the API as a dictionary.
        """
        params = self._clean_params(params or {})
        data = self._clean_params(data or {})
        response = self.session.request(
            method=method, url=self.url, params=params, data=data, headers=headers
        )
        try:
            return response.json()
        except Exception as e:
            print(f"Error: {e}. Response code: {response.status_code}")
            print(response.content)
            return {"error": str(e)}

    def get_ip(
        self, proxy_id: ProxyIdLike, check_spam: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Получение ip-адреса вашего прокси
        Данный запрос позволяет узнать, какой ip-адрес в данный момент выдает ваш прокси

        Response:
        {
            {
                status, //Статус операции, ok или err
                proxy_id, //Массив значений, где ключ - это идентификатор прокси, а значение - это ip-адрес, который он выдает
            }
        }

        :param proxy_id: Идентификатор прокси, которому нужно узнать ip-адрес
        :type proxy_id: int

        :return: Список ip-адресов
        :rtype: dict
        """
        params = {
            "command": "proxy_ip",
            "proxy_id": self._normalize_id_list(proxy_id),
            "check_spam": "true" if check_spam else None,
        }

        return self.request(params)

    def change_ip(
        self,
        proxy_key: str,
        user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        format: str = "json",
    ) -> Dict[str, Any]:
        """
        Изменение IP-адреса прокси
        Данный запрос не требует указания заголовка с авторизацией,
        необходимо указывать User-agent браузера.

        :param proxy_key: Ключ прокси
        :type proxy_key: str
        :param user_agent: User-Agent принадлежащий не боту
        :type user_agent: str
        :param format: Формат ответа (json или 0)
        :type format: str
        :return: Ответ от сервера
        :rtype: dict
        """
        url = f"https://changeip.mobileproxy.space/?proxy_key={proxy_key}&format={format}"
        headers = {"User-Agent": user_agent}

        response = self.session.get(url, headers=headers)
        return response.json()

    def get_price(
        self,
        id_country: ProxyIdLike,
        currency: Optional[str] = None,
        accept_language: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Получение цен на прокси в зависимости от страны.

        :param id_country: Идентификатор страны
        :type id_country: int
        :param currency: Валюта (usd или rub)
        :param accept_language: Язык ответа (en или ru)
        :return: Ответ от сервера с ценами
        :rtype: dict
        """
        params = {
            "command": "get_price",
            "id_country": self._normalize_id_list(id_country),
        }
        if currency is not None:
            params["currency"] = currency

        headers = {"Accept-Language": accept_language} if accept_language else None
        return self.request(params, headers=headers)

    def get_black_list(self, proxy_id: ProxyIdLike) -> Dict[str, Any]:
        """
        Получение черного списка оборудования и операторов.

        :param proxy_id: Идентификатор прокси
        :type proxy_id: int
        :return: Ответ от сервера с черным списком
        :rtype: dict
        """
        params = {"command": "get_black_list", "proxy_id": self._normalize_id_list(proxy_id)}
        return self.request(params)

    def add_operator_to_black_list(self, proxy_id: ProxyIdLike, operator_id: int) -> Dict[str, Any]:
        """
        Добавить оператора в черный список.

        :param proxy_id: Идентификатор прокси
        :type proxy_id: int
        :param operator_id: Идентификатор оператора
        :type operator_id: int
        :return: Ответ от сервера о статусе операции
        :rtype: dict
        """
        params = {
            "command": "add_operator_to_black_list",
            "proxy_id": self._normalize_id_list(proxy_id),
            "operator_id": operator_id,
        }
        return self.request(params)

    def remove_operator_from_black_list(self, proxy_id: ProxyIdLike, operator_id: int) -> Dict[str, Any]:
        """
        Удалить оператора из черного списка.

        :param proxy_id: Идентификатор прокси
        :type proxy_id: int
        :param operator_id: Идентификатор оператора
        :type operator_id: int
        :return: Ответ от сервера о статусе операции
        :rtype: dict
        """
        params = {
            "command": "remove_operator_black_list",
            "proxy_id": self._normalize_id_list(proxy_id),
            "operator_id": operator_id,
        }
        return self.request(params)

    def remove_black_list(
        self, proxy_id: ProxyIdLike, black_list_id: Optional[int] = None, eid: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Удалить записи из черного списка оборудования.

        :param proxy_id: Идентификатор прокси
        :type proxy_id: int
        :param black_list_id: Идентификатор записи
        :type black_list_id: int, optional
        :param eid: Идентификатор оборудования
        :type eid: int, optional
        :return: Ответ от сервера о статусе операции
        :rtype: dict
        """
        params = {
            "command": "remove_black_list",
            "proxy_id": self._normalize_id_list(proxy_id),
            "black_list_id": black_list_id,
            "eid": eid,
        }
        return self.request(params)

    def get_my_proxy(self, proxy_id: Optional[ProxyIdLike] = None) -> Dict[str, Any]:
        """
        Получение списка ваших активных прокси.

        :param proxy_id: Идентификатор прокси
        :type proxy_id: int
        :return: Ответ от сервера с активными прокси
        :rtype: dict
        """
        params = {"command": "get_my_proxy", "proxy_id": self._normalize_id_list(proxy_id)}
        return self.request(params)

    def change_proxy_login_password(self, proxy_id: ProxyIdLike, proxy_login: str, proxy_pass: str) -> Dict[str, Any]:
        """
        Изменение логина и пароля прокси.

        :param proxy_id: Идентификатор прокси
        :type proxy_id: int
        :param proxy_login: Новый логин
        :type proxy_login: str
        :param proxy_pass: Новый пароль
        :type proxy_pass: str
        :return: Ответ от сервера о статусе операции
        :rtype: dict
        """
        params = {
            "command": "change_proxy_login_password",
            "proxy_id": self._normalize_id_list(proxy_id),
            "proxy_login": proxy_login,
            "proxy_pass": proxy_pass,
        }
        return self.request(params)

    def reboot_proxy(self, proxy_id: int) -> Dict[str, Any]:
        """
        Перезагрузка прокси.

        :param proxy_id: Идентификатор прокси
        :type proxy_id: int
        :return: Ответ от сервера о статусе операции
        :rtype: dict
        """
        params = {"command": "reboot_proxy", "proxy_id": proxy_id}
        return self.request(params)

    def get_geo_operator_list(
        self,
        equipments_back_list: Optional[int] = None,
        operators_back_list: Optional[int] = None,
        show_count_null: Optional[int] = None,
        proxy_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Получение только доступного оборудования сгруппированного по ГЕО и оператору

        :param equipments_back_list: Исключить из списка содержимое черного списка оборудования
        :param operators_back_list: Исключить из списка содержимое черного списка операторов
        :param show_count_null: Показать нулевое количество, по умолчанию false
        :param proxy_id: Идентификатор прокси
        :return: Список доступного оборудования
        :rtype: dict
        """
        params = {
            "command": "get_geo_operator_list",
            "equipments_back_list": equipments_back_list,
            "operators_back_list": operators_back_list,
            "show_count_null": show_count_null,
            "proxy_id": proxy_id,
        }
        return self.request(params)

    def get_operators_list(self, geoid: Optional[ProxyIdLike] = None) -> Dict[str, Any]:
        """
        Получение списка операторов

        :param geoid: Идентификаторы ГЕО
        :type geoid: int или список
        :return: Список операторов
        :rtype: dict
        """
        params = {"command": "get_operators_list", "geoid": self._normalize_id_list(geoid)}
        return self.request(params)

    def get_id_country(
        self,
        only_avaliable: Optional[int] = None,
        accept_language: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Получение списка стран

        :param only_avaliable: Возвращать только доступные страны
        :param accept_language: Язык ответа (en или ru)
        :return: Список стран
        :rtype: dict
        """
        params = {"command": "get_id_country", "only_avaliable": only_avaliable}
        headers = {"Accept-Language": accept_language} if accept_language else None
        return self.request(params, headers=headers)

    def get_id_city(self, accept_language: Optional[str] = None) -> Dict[str, Any]:
        """
        Получение списка городов

        :param accept_language: Язык ответа (en или ru)
        :return: Список городов
        :rtype: dict
        """
        params = {"command": "get_id_city"}
        headers = {"Accept-Language": accept_language} if accept_language else None
        return self.request(params, headers=headers)

    def get_geo_list(
        self,
        proxy_id: Optional[int] = None,
        geoid: Optional[ProxyIdLike] = None,
    ) -> Dict[str, Any]:
        """
        Получение списка доступных ГЕО

        :param proxy_id: Идентификатор прокси
        :param geoid: Идентификаторы ГЕО
        :return: Список доступных ГЕО
        :rtype: dict
        """
        params = {
            "command": "get_geo_list",
            "proxy_id": proxy_id,
            "geoid": self._normalize_id_list(geoid),
        }
        return self.request(params)

    def change_equipment(
        self,
        proxy_id: ProxyIdLike,
        operator: Optional[str] = None,
        geoid: Optional[int] = None,
        add_to_black_list: Optional[int] = None,
        id_country: Optional[int] = None,
        id_city: Optional[int] = None,
        eid: Optional[int] = None,
        check_after_change: Optional[bool] = None,
        check_spam: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """
        Смена оборудования

        :param operator: Идентификатор оператора
        :param geoid: Идентификатор ГЕО
        :param proxy_id: Идентификатор прокси
        :param add_to_black_list: Добавить в черный список
        :param id_country: Идентификатор страны
        :param id_city: Идентификатор города
        :param eid: Идентификатор оборудования
        :param check_after_change: Проверить IP после смены
        :param check_spam: Проверить IP по базе спама
        :return: Результат смены оборудования
        :rtype: dict
        """
        params = {
            "command": "change_equipment",
            "operator": operator,
            "geoid": geoid,
            "proxy_id": self._normalize_id_list(proxy_id),
            "add_to_black_list": add_to_black_list,
            "id_country": id_country,
            "id_city": id_city,
            "eid": eid,
            "check_after_change": "true" if check_after_change else None,
            "check_spam": "true" if check_spam else None,
        }
        return self.request(params)

    def buy_proxy(
        self,
        period: int = 30,
        num: int = 1,
        proxy_id: Optional[ProxyIdLike] = None,
        geoid: Optional[int] = None,
        operator: Optional[str] = None,
        coupons_code: Optional[str] = None,
        id_country: Optional[int] = None,
        id_city: Optional[int] = None,
        amount_only: bool = False,
        auto_renewal: int = 1,
    ) -> Dict[str, Any]:
        """
        Покупка прокси

        :param operator: Идентификатор оператора
        :param geoid: Идентификатор ГЕО
        :param proxy_id: Идентификатор прокси
        :param period: Период покупки (по умолчанию 30)
        :param num: Количество прокси (по умолчанию 1)
        :param coupons_code: Код купона
        :param id_country: Идентификатор страны
        :param id_city: Идентификатор города
        :param auto_renewal: Автопродление
        :return: Результат покупки прокси
        :rtype: dict
        """
        params = {
            "command": "buyproxy",
            "operator": operator,
            "geoid": geoid,
            "proxy_id": self._normalize_id_list(proxy_id),
            "period": period,
            "num": num,
            "coupons_code": coupons_code,
            "id_country": id_country,
            "id_city": id_city,
            "auto_renewal": auto_renewal,
        }
        if amount_only:
            params["amount_only"] = "true"

        return self.request(params)

    def get_balance(self) -> Dict[str, Any]:
        """
        Получение баланса аккаунта

        :return: Баланс аккаунта
        :rtype: dict
        """
        params = {"command": "get_balance"}
        return self.request(params)

    def edit_proxy(
        self,
        proxy_id: ProxyIdLike,
        proxy_reboot_time: Optional[int] = None,
        proxy_ipauth: Optional[str] = None,
        proxy_auto_renewal: Optional[int] = None,
        proxy_auto_change_equipment: Optional[int] = None,
        proxy_comment: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Изменение настроек существующего прокси

        :param proxy_id: Идентификатор прокси
        :param proxy_reboot_time: Время смены ip-адреса
        :param proxy_ipauth: Список ip-адресов для авторизации
        :param proxy_auto_renewal: Автопродление
        :param proxy_auto_change_equipment: Автосмена оборудования
        :param proxy_comment: Комментарий к прокси
        :return: Результат изменения настроек прокси
        :rtype: dict
        """
        params = {
            "command": "edit_proxy",
            "proxy_id": self._normalize_id_list(proxy_id),
            "proxy_reboot_time": proxy_reboot_time,
            "proxy_ipauth": proxy_ipauth,
            "proxy_auto_renewal": proxy_auto_renewal,
            "proxy_auto_change_equipment": proxy_auto_change_equipment,
            "proxy_comment": proxy_comment,
        }
        return self.request(params)

    def get_ipstat(self) -> Dict[str, Any]:
        """
        Статистика IP-адресов мобильных прокси по ГЕО

        :return: Статистика IP-адресов
        :rtype: dict
        """
        params = {"command": "get_ipstat"}
        return self.request(params)

    def see_the_url_from_different_IPs(self, url: str, id_country: Optional[str] = None) -> Dict[str, Any]:
        """
        Получить содержимое страницы с разных IP

        :param url: Адрес страницы для проверки
        :param id_country: Список идентификаторов стран
        :return: Результат проверки страницы
        :rtype: dict
        """
        params = {
            "command": "see_the_url_from_different_IPs",
            "url": url,
            "id_country": id_country,
        }
        return self.request(data=params, method="POST")

    def get_task_result(self, tasks_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Получение результата выполнения задачи

        :param tasks_id: Идентификатор созданной задачи (опционально)
        :return: Результат выполнения задачи
        :rtype: dict
        """
        params = {"command": "tasks", "tasks_id": tasks_id}
        return self.request(params)

    def eid_available(self, eid: ProxyIdLike) -> Dict[str, Any]:
        """
        Выяснить занятость оборудования.

        :param eid: Идентификатор оборудования или список
        :return: Статус занятости оборудования
        :rtype: dict
        """
        params = {
            "command": "eid_avaliable",
            "eid": self._normalize_id_list(eid),
        }
        return self.request(params)

    def get_history(self, start: int = 0, length: int = 50) -> Dict[str, Any]:
        """
        Получить историю движения средств.

        :param start: Смещение
        :param length: Количество записей
        :return: История движения средств
        :rtype: dict
        """
        params = {"command": "get_history", "start": start, "length": length}
        return self.request(params)
