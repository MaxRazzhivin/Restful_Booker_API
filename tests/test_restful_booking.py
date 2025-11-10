import allure
import pytest
import requests

from constants import BASE_URL

@allure.suite("Bookings CRUD")
@allure.title("Создание, обновление и удаление брони")
class TestBookings:

    def test_create_booking(self, auth_session, booking_data):
        with allure.step('Создаем данные и создаем бронь'):
            data = booking_data()
            create_booking = auth_session.post(f'{BASE_URL}/booking', json = data)
            assert create_booking.status_code == 200

        with allure.step('Проверяем через GET'):
            booking_id = create_booking.json().get('bookingid')
            assert booking_id is not None, 'ID букинга не найден'

            assert create_booking.json()["booking"][
                       "firstname"] == data['firstname'], ("Заданное имя не "
                                                                   "совпадает")
            assert create_booking.json()["booking"][
                       "totalprice"] == data['totalprice'], ("Заданная стоимость "
                                                                     "неовпадает")

            get_booking = auth_session.get(f'{BASE_URL}/booking/{booking_id}')
            assert get_booking.status_code == 200
            assert get_booking.json()[
                       "lastname"] == data['lastname'], ("Заданная фамилия не "
                                                               "совпадает")

        with allure.step('Проверяем обновление данных через PUT'):
            updated_data = booking_data()
            put_booking = auth_session.put(f'{BASE_URL}/booking/{booking_id}', json=
                                           updated_data)
            assert put_booking.status_code == 200
            assert put_booking.json()['firstname'] == updated_data['firstname']
            assert put_booking.json()['lastname'] == updated_data['lastname']

        with allure.step('Сверяем обновленные данные в старом букинге'):
            get_booking = auth_session.get(f'{BASE_URL}/booking/{booking_id}')

            assert get_booking.json()['firstname'] == updated_data['firstname']


        with allure.step('Проверяем частичное обновление через PATCH'):
            patch_booking = auth_session.patch(f'{BASE_URL}/booking/{booking_id}', json=
            {
                'firstname': 'Alex',
                'lastname': 'Potter',
                'additionalneeds': 'laptop'
            })

            assert patch_booking.status_code == 200, f"PATCH не сработал: {patch_booking.text}"

        with allure.step('Делаем GET запрос для проверки изменения данных'):
            get_booking = auth_session.get(f'{BASE_URL}/booking/{booking_id}')

            assert patch_booking.json()['firstname'] == get_booking.json()['firstname']
            assert patch_booking.json()['lastname'] == get_booking.json()['lastname']
            assert patch_booking.json()['additionalneeds'] == get_booking.json()['additionalneeds']
            assert updated_data['totalprice'] == get_booking.json()['totalprice']

        with allure.step('Удаляем после себя бронь'):
            deleted_booking = auth_session.delete(f'{BASE_URL}/booking/{booking_id}')
            assert deleted_booking.status_code == 201

        with allure.step('Проверяем наличие после удаления'):
            get_booking = auth_session.get(f'{BASE_URL}/booking/{booking_id}')
            assert get_booking.status_code == 404





@allure.suite("Bookings Negative tests")
class TestBookingsNegative:
    def test_without_firstname_lastname(self, auth_session, booking_data):
        with allure.step('Проверяем создание букинга без обязательных полей'):
            negative_data = booking_data()
            negative_data.pop('lastname', None)
            negative_data.pop('firstname', None)
            negative_create = auth_session.post(f'{BASE_URL}/booking', json=negative_data)

            if negative_create.status_code == 200:
                pytest.xfail('Сервис не валидирует запрос с проверкой обязательных '
                             'полей')
            elif negative_create.status_code == 500:
                pytest.xfail('Сервис падает с 500 при отсутствии обязательных полей')
            else:
                assert negative_create.status_code in (400, 404), \
                    f"Ожидали 400 или 404, получили {negative_create.status_code}"

    def test_wrong_data_format(self, auth_session, booking_data):
        with allure.step('Проверяем негативный сценарий создания букинга - текст '
                         'вместа числа'):
            new_negative_data = booking_data()
            new_negative_data['totalprice'] = 'some_value_8734895_ldfjhgkjdfg'
            new_negative_create = auth_session.post(f'{BASE_URL}/booking',
                                                    json=new_negative_data)
            if new_negative_create.status_code == 200:
                pytest.xfail('Сервис не проверяет типы данных - должен падать')
            else:
                assert new_negative_create.status_code in (400, 404), \
                    f"Ожидали 400 или 404, получили {new_negative_create.status_code}"

    def test_update_nonexist_booking_id(self, auth_session, booking_data):
        with allure.step('Попытка обновления несуществующего ресурса'):
            negative_update = auth_session.put(f'{BASE_URL}/booking/478',
                                               json=booking_data())
            if negative_update.status_code == 200:
                pytest.xfail('Сервис не валидирует запрос с проверкой id букинга')
            else:
                assert negative_update.status_code in (400, 404, 405), \
                    f'Ожидали 400 или 404, получили {negative_update.status_code}'

    def test_delete_without_authorization(self, auth_session, booking_data):
        with allure.step('Создаем новый букинг с авторизацией и пробуем удалить без '
                         'авторизации'):
            new_booking = auth_session.post(f'{BASE_URL}/booking', json=booking_data())
            booking_id = new_booking.json().get('bookingid')
            delete_without_auth = requests.delete(f'{BASE_URL}/booking/{booking_id}')
            assert delete_without_auth.status_code == 403
