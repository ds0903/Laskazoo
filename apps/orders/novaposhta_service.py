"""
Сервіс для роботи з API Нової Пошти
Документація: https://developers.novaposhta.ua/
"""
import requests
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class NovaPoshtaAPI:
    """Клас для роботи з API Нової Пошти"""
    
    BASE_URL = "https://api.novaposhta.ua/v2.0/json/"
    
    def __init__(self):
        self.api_key = getattr(settings, 'NOVA_POSHTA_API_KEY', '')
        if not self.api_key:
            logger.warning("NOVA_POSHTA_API_KEY не налаштований в settings")
    
    def _make_request(self, model_name, called_method, method_properties=None):
        """Базовий метод для виконання запитів до API"""
        if not self.api_key:
            logger.error("API ключ Нової Пошти не налаштований")
            return None
        
        payload = {
            "apiKey": self.api_key,
            "modelName": model_name,
            "calledMethod": called_method,
            "methodProperties": method_properties or {}
        }
        
        try:
            response = requests.post(self.BASE_URL, json=payload, timeout=10)
            response.raise_for_status()
            result = response.json()
            
            if not result.get('success'):
                errors = result.get('errors', [])
                logger.error(f"Помилка API Нової Пошти: {errors}")
                return None
            
            return result.get('data', [])
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Помилка запиту до API Нової Пошти: {e}")
            return None
    
    def search_cities(self, query):
        """
        Пошук міст за назвою або індексом
        
        Args:
            query (str): Пошуковий запит (назва міста або індекс)
        
        Returns:
            list: Список міст з інформацією
        """
        print(f"🔍 NovaPoshtaAPI.search_cities: query='{query}'")
        print(f"🔑 NovaPoshtaAPI.search_cities: api_key={'SET' if self.api_key else 'NOT SET'}")
        
        # Спробуємо спочатку getCities (альтернативний метод)
        print(f"📦 NovaPoshtaAPI: Спробуємо getCities...")
        
        data = self._make_request(
            model_name="Address",
            called_method="getCities",
            method_properties={"FindByString": query}
        )
        
        print(f"📬 NovaPoshtaAPI getCities: data={data[:2] if data and len(data) > 0 else data}")
        
        if data and len(data) > 0:
            # getCities повертає масив міст напрямую
            cities = []
            for item in data:
                cities.append({
                    'ref': item.get('Ref', '') or item.get('DeliveryCity', ''),
                    'present': item.get('Description', '') + ', ' + item.get('AreaDescription', ''),
                    'main_description': item.get('Description', ''),
                    'area': item.get('AreaDescription', ''),
                    'region': item.get('RegionsDescription', ''),
                    'settlement_type': 'city'
                })
            print(f"✅ NovaPoshtaAPI getCities: Знайдено {len(cities)} міст")
            return cities
        
        # Якщо getCities не спрацював - пробуємо searchSettlements
        print(f"📦 NovaPoshtaAPI: Пробуємо searchSettlements...")
        
        method_properties = {
            "FindByString": query,
            "Limit": "50"
        }
        
        data = self._make_request(
            model_name="Address",
            called_method="searchSettlements",
            method_properties=method_properties
        )
        
        print(f"📬 NovaPoshtaAPI: Отримали відповідь, data type={type(data)}, length={len(data) if data else 0}")
        
        # DEBUG: Виводимо всю відповідь
        if data:
            print(f"🔍 DEBUG searchSettlements: {data}")
        
        if not data or not isinstance(data, list) or len(data) == 0:
            print("❌ NovaPoshtaAPI: Порожня відповідь")
            return []
        
        # API повертає масив з одним об'єктом, який містить Addresses
        addresses = data[0].get('Addresses', []) if data else []
        
        print(f"🏛️ NovaPoshtaAPI: Знайдено {len(addresses)} адрес")
        
        # Якщо нічого не знайдено - спробуємо з великої літери
        if len(addresses) == 0 and query:
            print(f"🔄 NovaPoshtaAPI: Пробуємо з великої літери...")
            capitalized_query = query.capitalize()
            
            retry_data = self._make_request(
                model_name="Address",
                called_method="searchSettlements",
                method_properties={
                    "FindByString": capitalized_query,
                    "Limit": "50"
                }
            )
            
            if retry_data and len(retry_data) > 0:
                addresses = retry_data[0].get('Addresses', [])
                print(f"✅ NovaPoshtaAPI: З великої літери знайдено {len(addresses)} адрес")
        
        # Форматуємо результати
        cities = []
        for item in addresses:
            cities.append({
                'ref': item.get('DeliveryCity', ''),  # Ref міста
                'present': item.get('Present', ''),    # Повна назва для відображення
                'main_description': item.get('MainDescription', ''),  # Назва міста
                'area': item.get('Area', ''),  # Область
                'region': item.get('Region', ''),  # Район
                'settlement_type': item.get('SettlementTypeCode', '')  # Тип населеного пункту
            })
        
        return cities
    
    def get_warehouses(self, city_ref, find_by_string=''):
        """
        Отримання списку відділень Нової Пошти в місті
        
        Args:
            city_ref (str): Ref міста
            find_by_string (str): Додатковий фільтр за номером відділення
        
        Returns:
            list: Список відділень
        """
        print(f"🏪 NovaPoshtaAPI.get_warehouses: city_ref='{city_ref}'")
        
        method_properties = {
            "CityRef": city_ref,
            "Limit": "100"
        }
        
        if find_by_string:
            method_properties["FindByString"] = find_by_string
        
        print(f"📦 NovaPoshtaAPI: Запит відділень з параметрами: {method_properties}")
        
        data = self._make_request(
            model_name="Address",
            called_method="getWarehouses",
            method_properties=method_properties
        )
        
        print(f"📬 NovaPoshtaAPI: Отримали {len(data) if data else 0} відділень")
        
        if not data:
            print("❌ NovaPoshtaAPI: Відділення не знайдено")
            return []
        
        # Форматуємо результати
        warehouses = []
        for item in data:
            warehouses.append({
                'ref': item.get('Ref', ''),  # Ref відділення
                'description': item.get('Description', ''),  # Повна назва
                'short_address': item.get('ShortAddress', ''),  # Коротка адреса
                'number': item.get('Number', ''),  # Номер відділення
                'type': item.get('TypeOfWarehouse', ''),  # Тип відділення
                'city_ref': item.get('CityRef', '')  # Ref міста
            })
        
        print(f"✅ NovaPoshtaAPI: Сформатовано {len(warehouses)} відділень")
        return warehouses
    
    def create_internet_document(self, order_data):
        """
        Створення експрес-накладної (відправлення)
        
        Args:
            order_data (dict): Дані замовлення
                - sender_ref: Ref відправника (ваш контрагент)
                - sender_contact_ref: Ref контакту відправника
                - sender_address_ref: Ref адреси відправника
                - recipient_name: ПІБ одержувача
                - recipient_phone: Телефон одержувача
                - recipient_city_ref: Ref міста одержувача
                - recipient_warehouse_ref: Ref відділення одержувача
                - cost: Оціночна вартість
                - weight: Вага (кг)
                - seats_amount: Кількість місць
                - description: Опис вантажу
                - payment_method: Спосіб оплати (Cash/NonCash)
                - backward_delivery_money: Сума зворотної доставки (для накладеного платежу)
        
        Returns:
            dict: Інформація про створену накладну або None
        """
        # Базові властивості методу
        # ДЛЯ ДЕБАГУ: симулюємо що товар ВЖЕ ОПЛАЧЕНИЙ
        print("💡 DEBUG: Товар оплачений, одержувач платить ТІЛЬКИ за доставку")
        
        method_properties = {
            "NewAddress": "1",  # Новий одержувач
            "PayerType": "Recipient",  # Платник - одержувач (тільки за доставку!)
            "PaymentMethod": "Cash",  # Готівка (за доставку, а не за товар!)
            "CargoType": "Parcel",  # Тип вантажу - посилка
            "ServiceType": "WarehouseWarehouse",  # Склад-склад
            "OptionsSeat": [{"volumetricVolume": "0.1", "volumetricWidth": "10", "volumetricLength": "10", "volumetricHeight": "10", "weight": "1"}],  # Обов'язково!
            
            # Відправник
            "CitySender": order_data.get('sender_city_ref', ''),
            "Sender": order_data.get('sender_ref', ''),
            "SenderAddress": order_data.get('sender_address_ref', ''),
            "ContactSender": order_data.get('sender_contact_ref', ''),
            "SendersPhone": order_data.get('sender_phone', ''),
            
            # Одержувач
            "CityRecipient": order_data.get('recipient_city_ref', ''),
            "RecipientAddress": order_data.get('recipient_warehouse_ref', ''),
            "RecipientName": order_data.get('recipient_name', ''),
            "RecipientType": "PrivatePerson",
            "RecipientsPhone": order_data.get('recipient_phone', ''),
            
            # Вантаж
            "Weight": str(order_data.get('weight', '1')),
            "SeatsAmount": str(order_data.get('seats_amount', '1')),
            "Description": order_data.get('description', 'Товар'),
            "Cost": str(order_data.get('cost', '100')),
            
            # Дата відправки
            "DateTime": order_data.get('date', ''),
        }
        
        # Зворотна доставка (накладений платіж)
        if order_data.get('backward_delivery_money'):
            method_properties.update({
                "BackwardDeliveryData": [{
                    "PayerType": "Recipient",
                    "CargoType": "Money",
                    "RedeliveryString": str(order_data['backward_delivery_money'])
                }]
            })
        
        data = self._make_request(
            model_name="InternetDocument",
            called_method="save",
            method_properties=method_properties
        )
        
        if data and len(data) > 0:
            return {
                'ref': data[0].get('Ref', ''),
                'cost_on_site': data[0].get('CostOnSite', ''),
                'estimated_delivery_date': data[0].get('EstimatedDeliveryDate', ''),
                'int_doc_number': data[0].get('IntDocNumber', ''),  # Номер ТТН
                'type_document': data[0].get('TypeDocument', '')
            }
        
        return None
    
    def get_counterparties(self):
        """
        Отримання списку контрагентів (відправників)
        Використовується для налаштування відправника
        
        Returns:
            list: Список контрагентів
        """
        data = self._make_request(
            model_name="Counterparty",
            called_method="getCounterparties",
            method_properties={"CounterpartyProperty": "Sender"}
        )
        
        if not data:
            return []
        
        counterparties = []
        for item in data:
            counterparties.append({
                'ref': item.get('Ref', ''),
                'description': item.get('Description', ''),
                'first_name': item.get('FirstName', ''),
                'last_name': item.get('LastName', ''),
                'middle_name': item.get('MiddleName', ''),
                'ownership_form': item.get('OwnershipForm', '')
            })
        
        return counterparties
    
    def get_counterparty_addresses(self, counterparty_ref):
        """
        Отримання адрес контрагента
        
        Args:
            counterparty_ref (str): Ref контрагента
        
        Returns:
            list: Список адрес
        """
        data = self._make_request(
            model_name="Counterparty",
            called_method="getCounterpartyAddresses",
            method_properties={"Ref": counterparty_ref}
        )
        
        if not data:
            return []
        
        addresses = []
        for item in data:
            addresses.append({
                'ref': item.get('Ref', ''),
                'description': item.get('Description', ''),
                'city_ref': item.get('CityRef', ''),
                'city_description': item.get('CityDescription', ''),
                'street_ref': item.get('StreetRef', ''),
                'building_number': item.get('BuildingNumber', '')
            })
        
        return addresses
    
    def get_counterparty_contact_persons(self, counterparty_ref):
        """
        Отримання контактних осіб контрагента
        
        Args:
            counterparty_ref (str): Ref контрагента
        
        Returns:
            list: Список контактних осіб
        """
        data = self._make_request(
            model_name="Counterparty",
            called_method="getCounterpartyContactPersons",
            method_properties={"Ref": counterparty_ref}
        )
        
        if not data:
            return []
        
        contacts = []
        for item in data:
            contacts.append({
                'ref': item.get('Ref', ''),
                'description': item.get('Description', ''),
                'phones': item.get('Phones', '')
            })
        
        return contacts
    
    def get_document_tracking(self, ttn_number):
        """
        Отримання статусу відстеження ТТН
        
        Args:
            ttn_number (str): Номер ТТН
        
        Returns:
            dict: Інформація про статус або None
        """
        data = self._make_request(
            model_name="TrackingDocument",
            called_method="getStatusDocuments",
            method_properties={"Documents": [{"DocumentNumber": ttn_number}]}
        )
        
        if not data or len(data) == 0:
            return None
        
        item = data[0]
        
        return {
            'number': item.get('Number', ''),
            'status': item.get('Status', ''),
            'status_code': item.get('StatusCode', ''),
            'recipient_date_time': item.get('RecipientDateTime', ''),
            'recipient_full_name': item.get('RecipientFullName', ''),
            'warehouse_recipient': item.get('WarehouseRecipient', ''),
            'city_sender': item.get('CitySender', ''),
            'city_recipient': item.get('CityRecipient', ''),
            'date_created': item.get('DateCreated', ''),
            'date_scan': item.get('DateScan', ''),
            'scheduled_delivery_date': item.get('ScheduledDeliveryDate', ''),
            'actual_delivery_date': item.get('ActualDeliveryDate', ''),
            'redelivery_num': item.get('RedeliveryNum', ''),
            'phone_recipient': item.get('PhoneRecipient', ''),
        }


# Singleton instance
nova_poshta_api = NovaPoshtaAPI()
