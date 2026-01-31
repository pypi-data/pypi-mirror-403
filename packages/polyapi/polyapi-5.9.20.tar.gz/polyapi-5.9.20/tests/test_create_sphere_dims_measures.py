#!/usr/bin/python3
"""
Юнит-тесты для метода create_sphere (параметры dims, measures) из business_scenarios.py
"""

import pytest

from polymatica.business_scenarios import BusinessLogic
from tests.const import TEST_SQL_PARAMS


class TestCreateSphereDimsMeasures:
    """Тесты для метода create_sphere (параметры dims, measures)"""

    @pytest.fixture
    def mock_business_logic(
        self, mocker, mock_server_codes, mock_config, mock_execute_manager_command
    ):
        # Мокаем только то, что нужно для работы без сервера
        mock_auth = mocker.patch("polymatica.business_scenarios.Authorization")
        mock_auth_instance = mocker.Mock()
        mock_auth_instance.login.return_value = ("session_id", "uuid", "5.9.13", "v2")
        mock_auth.return_value = mock_auth_instance

        mocker.patch(
            "polymatica.business_scenarios.BusinessLogic._get_interface_config",
            return_value=mock_config,
        )
        mocker.patch("polymatica.business_scenarios.Executor")

        # Создаем реальный экземпляр BusinessLogic
        bl = BusinessLogic(
            url="https://test.polymatica.ru/", login="test", password="test"
        )

        bl.server_codes = mock_server_codes
        bl.config = mock_config
        bl.logger = mocker.Mock()
        bl.cube_id = "test_cube_id"

        # Мокаем только те методы, которые делают реальные запросы к серверу
        bl.execute_manager_command = mocker.Mock(
            side_effect=mock_execute_manager_command
        )
        bl.get_cubes_list = mocker.Mock(return_value=[])

        bl.h.upload_file_to_server = mocker.Mock(return_value="datasource_test_id")

        return bl

    def test_dims_invalid_keys(self, mock_business_logic):
        """Тест валидации недопустимых ключей в параметре dims"""
        invalid_keys = ["invalid_key", "dims_mode", "custom_dims", "dimensions"]
        for invalid_key in invalid_keys:
            with pytest.raises(ValueError, match='Invalid key'):
                mock_business_logic.create_sphere(
                    cube_name="test_cube",
                    source_name="test_source_12345",
                    file_type="psql",
                    sql_params=TEST_SQL_PARAMS,
                    dims={invalid_key: "value"},
                )

    @pytest.mark.parametrize(
        "dims_list_mode",
        ["blacklist", "whitelist"],
    )
    def test_dims_list_mode_validation(self, mock_business_logic, dims_list_mode):
        """Тест валидации режима работы списка размерностей"""
        mock_business_logic.create_sphere(
            cube_name="test_cube",
            source_name="test_source_12345",
            file_type="psql",
            sql_params=TEST_SQL_PARAMS,
            dims={
                "dims_list_mode": dims_list_mode,
                "dims_list": ["date", "latitude"],
            },
        )

    def test_dims_list_mode_invalid(self, mock_business_logic):
        """Тест валидации некорректного режима работы списка размерностей"""
        invalid_modes = ["invalid", "black", ""]
        for invalid_mode in invalid_modes:
            with pytest.raises(ValueError, match='must be "blacklist" or "whitelist"'):
                mock_business_logic.create_sphere(
                    cube_name="test_cube",
                    source_name="test_source_12345",
                    file_type="psql",
                    sql_params=TEST_SQL_PARAMS,
                    dims={"dims_list_mode": invalid_mode},
                )

    def test_dims_list_type_validation(self, mock_business_logic):
        """Тест валидации типа dims_list (должен быть списком)"""
        invalid_types = ["string", 123, {"key": "value"}]
        for invalid_type in invalid_types:
            with pytest.raises(ValueError, match='must be list'):
                mock_business_logic.create_sphere(
                    cube_name="test_cube",
                    source_name="test_source_12345",
                    file_type="psql",
                    sql_params=TEST_SQL_PARAMS,
                    dims={"dims_list": invalid_type},
                )

    def test_dims_list_items_type_validation(self, mock_business_logic):
        """Тест валидации типа элементов dims_list (должны быть строками)"""
        invalid_items = [[123], [{"key": "value"}], [None], [["nested"]]]
        for invalid_item in invalid_items:
            with pytest.raises(ValueError, match='must be of type str'):
                mock_business_logic.create_sphere(
                    cube_name="test_cube",
                    source_name="test_source_12345",
                    file_type="psql",
                    sql_params=TEST_SQL_PARAMS,
                    dims={"dims_list": invalid_item},
                )

    def test_dims_list_whitelist_mode(self, mock_business_logic, mocker):
        """Тест работы режима whitelist для dims_list"""
        mock_business_logic.create_sphere(
            cube_name="test_cube",
            source_name="test_source_12345",
            file_type="psql",
            sql_params=TEST_SQL_PARAMS,
            dims={
                "dims_list_mode": "whitelist",
                "dims_list": ["date", "latitude", "longitude"],
            },
        )

        # Проверяем, что в последнем вызове execute_manager_command переданы правильные dims
        last_call = mock_business_logic.execute_manager_command.call_args_list[-1]
        assert "dims" in last_call.kwargs
        assert len(last_call.kwargs["dims"]) == 3
        dim_names = [d["name"] for d in last_call.kwargs["dims"]]
        assert "date" in dim_names
        assert "latitude" in dim_names
        assert "longitude" in dim_names

    def test_dims_list_blacklist_mode(self, mock_business_logic):
        """Тест работы режима blacklist для dims_list"""

        mock_business_logic.create_sphere(
            cube_name="test_cube",
            source_name="test_source_12345",
            file_type="psql",
            sql_params=TEST_SQL_PARAMS,
            dims={
                "dims_list_mode": "blacklist",
                "dims_list": ["datetime"],
            },
        )

        # Проверяем, что в последнем вызове execute_manager_command переданы правильные dims
        last_call = mock_business_logic.execute_manager_command.call_args_list[-1]
        assert "dims" in last_call.kwargs
        dim_names = [d["name"] for d in last_call.kwargs["dims"]]
        assert "datetime" not in dim_names  # datetime должна быть исключена
        assert "date" in dim_names
        assert "latitude" in dim_names

    def test_dims_list_default_mode(self, mock_business_logic):
        """Тест режима по умолчанию (whitelist) для dims_list"""
        mock_business_logic.create_sphere(
            cube_name="test_cube",
            source_name="test_source_12345",
            file_type="psql",
            sql_params=TEST_SQL_PARAMS,
            dims={
                "dims_list": ["date", "latitude"],
                # dims_list_mode не указан, должен использоваться whitelist по умолчанию
            },
        )

        # Проверяем, что в последнем вызове execute_manager_command переданы правильные dims
        last_call = mock_business_logic.execute_manager_command.call_args_list[-1]
        assert "dims" in last_call.kwargs
        assert len(last_call.kwargs["dims"]) == 2
        dim_names = [d["name"] for d in last_call.kwargs["dims"]]
        assert "date" in dim_names
        assert "latitude" in dim_names

    def test_dims_custom_list_type_validation(self, mock_business_logic):
        """Тест валидации типа dims_custom_list (должен быть списком)"""
        invalid_types = ["string", 123, {"key": "value"}]
        for invalid_type in invalid_types:
            with pytest.raises(ValueError, match='must be list of dicts'):
                mock_business_logic.create_sphere(
                    cube_name="test_cube",
                    source_name="test_source_12345",
                    file_type="psql",
                    sql_params=TEST_SQL_PARAMS,
                    dims={"dims_custom_list": invalid_type},
                )

    def test_dims_custom_list_items_type_validation(self, mock_business_logic):
        """Тест валидации типа элементов dims_custom_list (должны быть словарями)"""
        invalid_items = [["string"], [123], [None]]
        for invalid_item in invalid_items:
            with pytest.raises(ValueError, match='must be dict'):
                mock_business_logic.create_sphere(
                    cube_name="test_cube",
                    source_name="test_source_12345",
                    file_type="psql",
                    sql_params=TEST_SQL_PARAMS,
                    dims={"dims_custom_list": invalid_item},
                )

    def test_dims_custom_list_source_column_validation(self, mock_business_logic):
        """Тест валидации source_column в dims_custom_list"""
        invalid_source_columns = [None, 123, [], {}]
        for invalid_source_column in invalid_source_columns:
            with pytest.raises(ValueError, match='must be of type str'):
                mock_business_logic.create_sphere(
                    cube_name="test_cube",
                    source_name="test_source_12345",
                    file_type="psql",
                    sql_params=TEST_SQL_PARAMS,
                    dims={
                        "dims_custom_list": [
                            {"source_column": invalid_source_column}
                        ]
                    },
                )

    def test_dims_custom_list_source_column_required(self, mock_business_logic):
        """Тест обязательности поля source_column в dims_custom_list"""
        with pytest.raises(ValueError, match='must be of type str'):
            mock_business_logic.create_sphere(
                cube_name="test_cube",
                source_name="test_source_12345",
                file_type="psql",
                sql_params=TEST_SQL_PARAMS,
                dims={
                    "dims_custom_list": [
                        {"dim_name": "test_dim"}  # source_column отсутствует
                    ]
                },
            )

    def test_dims_custom_list_duplicate_source_column(self, mock_business_logic):
        """Тест валидации уникальности source_column в dims_custom_list"""
        with pytest.raises(ValueError, match='Duplicate source_column'):
            mock_business_logic.create_sphere(
                cube_name="test_cube",
                source_name="test_source_12345",
                file_type="psql",
                sql_params=TEST_SQL_PARAMS,
                dims={
                    "dims_custom_list": [
                        {"source_column": "date"},
                        {"source_column": "date"},  # дубликат
                    ]
                },
            )

    def test_dims_custom_list_duplicate_source_column_case_insensitive(
        self, mock_business_logic
    ):
        """Тест валидации уникальности source_column (регистронезависимо)"""
        with pytest.raises(ValueError, match='Duplicate source_column'):
            mock_business_logic.create_sphere(
                cube_name="test_cube",
                source_name="test_source_12345",
                file_type="psql",
                sql_params=TEST_SQL_PARAMS,
                dims={
                    "dims_custom_list": [
                        {"source_column": "Date"},
                        {"source_column": "date"},  # дубликат (разный регистр)
                    ]
                },
            )

    def test_dims_custom_list_dim_name_validation(self, mock_business_logic):
        """Тест валидации dim_name в dims_custom_list"""
        invalid_dim_names = [123, [], {}]
        for invalid_dim_name in invalid_dim_names:
            with pytest.raises(ValueError, match='must be str'):
                mock_business_logic.create_sphere(
                    cube_name="test_cube",
                    source_name="test_source_12345",
                    file_type="psql",
                    sql_params=TEST_SQL_PARAMS,
                    dims={
                        "dims_custom_list": [
                            {
                                "source_column": "date",
                                "dim_name": invalid_dim_name,
                            }
                        ]
                    },
                )

    def test_dims_custom_list_dim_name_optional(self, mock_business_logic):
        """Тест опциональности поля dim_name в dims_custom_list"""

        mock_business_logic.create_sphere(
            cube_name="test_cube",
            source_name="test_source_12345",
            file_type="psql",
            sql_params=TEST_SQL_PARAMS,
            dims={
                "dims_list": ["date"],
                "dims_custom_list": [
                    {"source_column": "date"}  # dim_name не указан
                ]
            },
        )

        # Проверяем, что в последнем вызове execute_manager_command переданы правильные dims
        last_call = mock_business_logic.execute_manager_command.call_args_list[-1]
        assert "dims" in last_call.kwargs
        assert len(last_call.kwargs["dims"]) == 1
        assert last_call.kwargs["dims"][0]["name"] == "date"

    def test_dims_custom_list_date_details_type_validation(self, mock_business_logic):
        """Тест валидации типа date_details (должен быть списком)"""
        invalid_types = ["string", 123, {"key": "value"}]
        for invalid_type in invalid_types:
            with pytest.raises(ValueError, match='must be list of strings'):
                mock_business_logic.create_sphere(
                    cube_name="test_cube",
                    source_name="test_source_12345",
                    file_type="psql",
                    sql_params=TEST_SQL_PARAMS,
                    dims={
                        "dims_custom_list": [
                            {
                                "source_column": "date",
                                "date_details": invalid_type,
                            }
                        ]
                    },
                )

    def test_dims_custom_list_date_details_items_type_validation(
        self, mock_business_logic
    ):
        """Тест валидации типа элементов date_details (должны быть строками)"""
        invalid_items = [[123], [["nested"]], [None], [{}]]
        for invalid_item in invalid_items:
            with pytest.raises(ValueError, match='must be of type str'):
                mock_business_logic.create_sphere(
                    cube_name="test_cube",
                    source_name="test_source_12345",
                    file_type="psql",
                    sql_params=TEST_SQL_PARAMS,
                    dims={
                        "dims_custom_list": [
                            {
                                "source_column": "date",
                                "date_details": invalid_item,
                            }
                        ]
                    },
                )

    @pytest.mark.parametrize(
        "source_column,date_detail",
        [
            ("datetime", "year"),
            ("datetime", "quarter"),
            ("datetime", "month"),
            ("datetime", "week"),
            ("datetime", "dow"),
            ("datetime", "day"),
            ("datetime", "date"),
            ("datetime", "time"),
            ("datetime", "hour"),
            ("datetime", "minute"),
            ("datetime", "second"),
            ("date", "year"),
            ("date", "quarter"),
            ("date", "month"),
            ("date", "week"),
            ("date", "dow"),
            ("date", "day"),
            ("date", "date"),
            ("time", "time"),
            ("time", "hour"),
            ("time", "minute"),
            ("time", "second"),
        ],
    )
    def test_dims_custom_list_date_details_valid_values(
        self, mock_business_logic, source_column, date_detail
    ):
        """Тест валидных значений в date_details для разных типов размерностей"""
        mock_business_logic.create_sphere(
            cube_name="test_cube",
            source_name="test_source_12345",
            file_type="psql",
            sql_params=TEST_SQL_PARAMS,
            dims={
                "dims_custom_list": [
                    {
                        "source_column": source_column,
                        "date_details": [date_detail],
                    }
                ]
            },
        )

    def test_dims_custom_list_date_details_invalid_value(self, mock_business_logic):
        """Тест невалидных значений в date_details"""
        invalid_values = ["invalid", "year_month", "date_time", "day_of_week", ""]
        for invalid_value in invalid_values:
            with pytest.raises(ValueError, match='is not allowed'):
                mock_business_logic.create_sphere(
                    cube_name="test_cube",
                    source_name="test_source_12345",
                    file_type="psql",
                    sql_params=TEST_SQL_PARAMS,
                    dims={
                        "dims_custom_list": [
                            {
                                "source_column": "date",
                                "date_details": [invalid_value],
                            }
                        ]
                    },
                )

    def test_dims_custom_list_date_details_multiple_values(self, mock_business_logic):
        """Тест нескольких значений в date_details"""
        mock_business_logic.create_sphere(
            cube_name="test_cube",
            source_name="test_source_12345",
            file_type="psql",
            sql_params=TEST_SQL_PARAMS,
            dims={
                "dims_custom_list": [
                    {
                        "source_column": "datetime",
                        "date_details": ["date", "year", "month", "quarter"],
                    }
                ]
            },
        )

    @pytest.mark.parametrize(
        "date_name, invalid_name",
        [
            (date_name, invalid_name)
            for date_name in ["date_orig_name", "date_gen_name"]
            for invalid_name in [123, [], {}]
        ],
    )
    def test_dims_custom_list_date_orig_and_gen_name_validation(
        self, mock_business_logic, date_name, invalid_name
    ):
        """Тест валидации date_orig_name и date_gen_name в dims_custom_list"""
        with pytest.raises(ValueError, match='must be of type str'):
            mock_business_logic.create_sphere(
                cube_name="test_cube",
                source_name="test_source_12345",
                file_type="psql",
                sql_params=TEST_SQL_PARAMS,
                dims={
                    "dims_custom_list": [
                        {
                            "source_column": "date",
                            date_name: invalid_name,
                        }
                    ]
                },
            )

    def test_dims_custom_list_date_names_equal_error(self, mock_business_logic):
        """Тест ошибки при одинаковых значениях date_orig_name и date_gen_name"""
        for date_gen_name in ("Дата", "дата"):
            with pytest.raises(ValueError, match='must be different'):
                mock_business_logic.create_sphere(
                    cube_name="test_cube",
                    source_name="test_source_12345",
                    file_type="psql",
                    sql_params=TEST_SQL_PARAMS,
                    dims={
                        "dims_custom_list": [
                            {
                                "source_column": "date",
                                "date_orig_name": "Дата",
                                "date_gen_name": date_gen_name,  # совпадает с date_orig_name
                            }
                        ]
                    },
                )

    def test_dims_custom_list(self, mock_business_logic):
        """Тест полного примера использования dims_custom_list со всеми параметрами"""

        mock_business_logic.create_sphere(
            cube_name="test_cube",
            source_name="test_source_12345",
            file_type="psql",
            sql_params=TEST_SQL_PARAMS,
            dims={
                "dims_custom_list": [
                    {
                        "source_column": "datetime",
                        "dim_name": "ДатаВремя",
                        "date_details": ["date", "year", "month", "quarter", "week"],
                        "date_orig_name": "ИсходнаяДата",
                        "date_gen_name": "ДатаПроизводная",
                    },
                    {
                        "source_column": "date",
                        "dim_name": "Дата",
                        "date_details": ["year", "quarter", "month"],
                    },
                ]
            },
        )

        # Проверяем, что в последнем вызове execute_manager_command переданы правильные dims
        last_call = mock_business_logic.execute_manager_command.call_args_list[-1]
        assert "dims" in last_call.kwargs
        dim_names = [d["name"] for d in last_call.kwargs["dims"]]
        assert "ДатаВремя" in dim_names
        assert "Дата" in dim_names

    def test_dims_combined_usage(self, mock_business_logic, mocker):
        """Тест использования dims_list вместе с dims_custom_list"""
        mock_business_logic.create_sphere(
            cube_name="test_cube",
            source_name="test_source_12345",
            file_type="psql",
            sql_params=TEST_SQL_PARAMS,
            dims={
                "dims_list_mode": "blacklist",
                "dims_list": ["latitude"],
                "dims_custom_list": [
                    {
                        "source_column": "date",
                        "dim_name": "Дата",
                        "date_details": ["year", "month"],
                    }
                ],
            },
        )

        # Проверяем, что в последнем вызове execute_manager_command переданы правильные dims
        last_call = mock_business_logic.execute_manager_command.call_args_list[-1]
        assert "dims" in last_call.kwargs
        assert len(last_call.kwargs["dims"]) == 4
        dim_names = [d["name"] for d in last_call.kwargs["dims"]]
        assert "Дата" in dim_names
        assert not "latitude" in dim_names

    def test_measures_invalid_keys(self, mock_business_logic):
        """Тест валидации недопустимых ключей в параметре measures"""
        invalid_keys = ["invalid_key", "measures_mode", "custom_measures", "facts"]
        for invalid_key in invalid_keys:
            with pytest.raises(ValueError, match='Invalid key'):
                mock_business_logic.create_sphere(
                    cube_name="test_cube",
                    source_name="test_source_12345",
                    file_type="psql",
                    sql_params=TEST_SQL_PARAMS,
                    measures={invalid_key: "value"},
                )

    @pytest.mark.parametrize(
        "measures_list_mode",
        ["blacklist", "whitelist"],
    )
    def test_measures_list_mode_validation(self, mock_business_logic, mocker, measures_list_mode):
        """Тест валидации режима работы списка фактов"""
        # Мокируем get_and_process_dims_and_measures
        expected_dims = [
            {"id": "dim1", "name": "date", "type": 6, "mark": 1, "field_id": "f1", "db_field": "date", "update_ts": 0,
             "datasource": "test_source", "field_type": "field"},
        ]
        if measures_list_mode == "whitelist":
            expected_measures = [
                {"id": "m1", "name": "latitude", "mark": 1, "nulls_allowed": False, "field_id": "f2",
                 "db_field": "latitude", "update_ts": 0, "datasource": "test_source", "field_type": "field"},
                {"id": "m2", "name": "longitude", "mark": 1, "nulls_allowed": False, "field_id": "f3",
                 "db_field": "longitude", "update_ts": 0, "datasource": "test_source", "field_type": "field"},
            ]
        else:  # blacklist
            expected_measures = [
                {"id": "m2", "name": "longitude", "mark": 1, "nulls_allowed": False, "field_id": "f3",
                 "db_field": "longitude", "update_ts": 0, "datasource": "test_source", "field_type": "field"},
            ]
        mock_business_logic.h.get_and_process_dims_and_measures = mocker.Mock(
            return_value=(expected_dims, expected_measures)
        )

        mock_business_logic.create_sphere(
            cube_name="test_cube",
            source_name="test_source_12345",
            file_type="psql",
            sql_params=TEST_SQL_PARAMS,
            measures={
                "measures_list_mode": measures_list_mode,
                "measures_list": ["latitude", "longitude"],
            },
        )

        # Проверяем, что в последнем вызове execute_manager_command переданы правильные facts
        last_call = mock_business_logic.execute_manager_command.call_args_list[-1]
        assert "facts" in last_call.kwargs
        if measures_list_mode == "whitelist":
            assert len(last_call.kwargs["facts"]) == 2
            measure_names = [m["name"] for m in last_call.kwargs["facts"]]
            assert "latitude" in measure_names
            assert "longitude" in measure_names
        else:  # blacklist
            measure_names = [m["name"] for m in last_call.kwargs["facts"]]
            assert "latitude" not in measure_names

    def test_measures_list_mode_invalid(self, mock_business_logic):
        """Тест валидации некорректного режима работы списка фактов"""
        invalid_modes = ["invalid", "black", "white", "list", ""]
        for invalid_mode in invalid_modes:
            with pytest.raises(ValueError, match='must be "blacklist" or "whitelist"'):
                mock_business_logic.create_sphere(
                    cube_name="test_cube",
                    source_name="test_source_12345",
                    file_type="psql",
                    sql_params=TEST_SQL_PARAMS,
                    measures={"measures_list_mode": invalid_mode},
                )

    def test_measures_list_type_validation(self, mock_business_logic):
        """Тест валидации типа measures_list (должен быть списком)"""
        invalid_types = ["string", 123, {"key": "value"}]
        for invalid_type in invalid_types:
            with pytest.raises(ValueError, match='must be list'):
                mock_business_logic.create_sphere(
                    cube_name="test_cube",
                    source_name="test_source_12345",
                    file_type="psql",
                    sql_params=TEST_SQL_PARAMS,
                    measures={"measures_list": invalid_type},
                )

    def test_measures_list_items_type_validation(self, mock_business_logic):
        """Тест валидации типа элементов measures_list (должны быть строками)"""
        invalid_items = [[123], [{"key": "value"}], [None], [["nested"]]]
        for invalid_item in invalid_items:
            with pytest.raises(ValueError, match='must be of type str'):
                mock_business_logic.create_sphere(
                    cube_name="test_cube",
                    source_name="test_source_12345",
                    file_type="psql",
                    sql_params=TEST_SQL_PARAMS,
                    measures={"measures_list": invalid_item},
                )

    def test_measures_list_whitelist_mode(self, mock_business_logic, mocker):
        """Тест работы режима whitelist для measures_list"""
        expected_dims = [
            {"id": "dim1", "name": "date", "type": 6, "mark": 1, "field_id": "f1", "db_field": "date",
             "update_ts": 0, "datasource": "test_source", "field_type": "field"},
        ]
        expected_measures = [
            {"id": "m1", "name": "latitude", "mark": 1, "nulls_allowed": False, "field_id": "f2",
             "db_field": "latitude", "update_ts": 0, "datasource": "test_source", "field_type": "field"},
            {"id": "m2", "name": "longitude", "mark": 1, "nulls_allowed": False, "field_id": "f3",
             "db_field": "longitude", "update_ts": 0, "datasource": "test_source", "field_type": "field"},
        ]
        mock_business_logic.h.get_and_process_dims_and_measures = mocker.Mock(
            return_value=(expected_dims, expected_measures)
        )

        mock_business_logic.create_sphere(
            cube_name="test_cube",
            source_name="test_source_12345",
            file_type="psql",
            sql_params=TEST_SQL_PARAMS,
            measures={
                "measures_list_mode": "whitelist",
                "measures_list": ["latitude", "longitude"],
            },
        )

        # Проверяем, что в последнем вызове execute_manager_command переданы правильные facts
        last_call = mock_business_logic.execute_manager_command.call_args_list[-1]
        assert "facts" in last_call.kwargs
        assert len(last_call.kwargs["facts"]) == 2
        measure_names = [m["name"] for m in last_call.kwargs["facts"]]
        assert "latitude" in measure_names
        assert "longitude" in measure_names

    def test_measures_list_blacklist_mode(self, mock_business_logic, mocker):
        """Тест работы режима blacklist для measures_list"""
        # Мокируем get_and_process_dims_and_measures
        expected_dims = [
            {"id": "dim1", "name": "date", "type": 6, "mark": 1, "field_id": "f1", "db_field": "date",
             "update_ts": 0, "datasource": "test_source", "field_type": "field"},
        ]
        expected_measures = [
            {"id": "m2", "name": "longitude", "mark": 1, "nulls_allowed": False, "field_id": "f3",
             "db_field": "longitude", "update_ts": 0, "datasource": "test_source", "field_type": "field"},
        ]
        mock_business_logic.h.get_and_process_dims_and_measures = mocker.Mock(
            return_value=(expected_dims, expected_measures)
        )

        mock_business_logic.create_sphere(
            cube_name="test_cube",
            source_name="test_source_12345",
            file_type="psql",
            sql_params=TEST_SQL_PARAMS,
            measures={
                "measures_list_mode": "blacklist",
                "measures_list": ["latitude"],
            },
        )

        # Проверяем, что в последнем вызове execute_manager_command переданы правильные facts
        last_call = mock_business_logic.execute_manager_command.call_args_list[-1]
        assert "facts" in last_call.kwargs
        measure_names = [m["name"] for m in last_call.kwargs["facts"]]
        assert "latitude" not in measure_names  # latitude должна быть исключена
        assert "longitude" in measure_names

    def test_measures_list_default_mode(self, mock_business_logic):
        """Тест режима по умолчанию (whitelist) для measures_list"""

        mock_business_logic.create_sphere(
            cube_name="test_cube",
            source_name="test_source_12345",
            file_type="psql",
            sql_params=TEST_SQL_PARAMS,
            measures={
                "measures_list": ["latitude", "longitude"],
                # measures_list_mode не указан, должен использоваться whitelist по умолчанию
            },
        )

        # Проверяем, что в последнем вызове execute_manager_command переданы правильные facts
        last_call = mock_business_logic.execute_manager_command.call_args_list[-1]
        assert "facts" in last_call.kwargs
        assert len(last_call.kwargs["facts"]) == 2
        measure_names = [m["name"] for m in last_call.kwargs["facts"]]
        assert "latitude" in measure_names
        assert "longitude" in measure_names

    def test_measures_custom_list_type_validation(self, mock_business_logic):
        """Тест валидации типа measures_custom_list (должен быть списком)"""
        invalid_types = ["string", 123, {"key": "value"}]
        for invalid_type in invalid_types:
            with pytest.raises(ValueError, match='must be list of dicts'):
                mock_business_logic.create_sphere(
                    cube_name="test_cube",
                    source_name="test_source_12345",
                    file_type="psql",
                    sql_params=TEST_SQL_PARAMS,
                    measures={"measures_custom_list": invalid_type},
                )

    def test_measures_custom_list_items_type_validation(self, mock_business_logic):
        """Тест валидации типа элементов measures_custom_list (должны быть словарями)"""
        invalid_items = [["string"], [123], [None]]
        for invalid_item in invalid_items:
            with pytest.raises(ValueError, match='must be dict'):
                mock_business_logic.create_sphere(
                    cube_name="test_cube",
                    source_name="test_source_12345",
                    file_type="psql",
                    sql_params=TEST_SQL_PARAMS,
                    measures={"measures_custom_list": invalid_item},
                )

    def test_measures_custom_list_source_column_validation(self, mock_business_logic):
        """Тест валидации source_column в measures_custom_list"""
        invalid_source_columns = [None, 123, [], {}]
        for invalid_source_column in invalid_source_columns:
            with pytest.raises(ValueError, match='must be specified and'):
                mock_business_logic.create_sphere(
                    cube_name="test_cube",
                    source_name="test_source_12345",
                    file_type="psql",
                    sql_params=TEST_SQL_PARAMS,
                    measures={
                        "measures_custom_list": [
                            {"source_column": invalid_source_column}
                        ]
                    },
                )

    def test_measures_custom_list_source_column_required(self, mock_business_logic):
        """Тест обязательности поля source_column в measures_custom_list"""
        with pytest.raises(ValueError, match='must be specified and'):
            mock_business_logic.create_sphere(
                cube_name="test_cube",
                source_name="test_source_12345",
                file_type="psql",
                sql_params=TEST_SQL_PARAMS,
                measures={
                    "measures_custom_list": [
                        {"measure_name": "test_measure"}  # source_column отсутствует
                    ]
                },
            )

    @pytest.mark.parametrize(
        "source_column1, source_column2",
        [
            ("latitude", "latitude"),
            ("Latitude", "latitude"),
        ],
    )
    def test_measures_custom_list_duplicate_source_column(self, mock_business_logic, source_column1, source_column2):
        """Тест валидации уникальности source_column в measures_custom_list"""
        with pytest.raises(ValueError, match='Duplicate source_column'):
            mock_business_logic.create_sphere(
                cube_name="test_cube",
                source_name="test_source_12345",
                file_type="psql",
                sql_params=TEST_SQL_PARAMS,
                measures={
                    "measures_custom_list": [
                        {"source_column": source_column1},
                        {"source_column": source_column2},  # дубликат
                    ]
                },
            )

    def test_measures_custom_list_measure_name_validation(self, mock_business_logic):
        """Тест валидации measure_name в measures_custom_list"""
        invalid_measure_names = [123, [], {}]
        for invalid_measure_name in invalid_measure_names:
            with pytest.raises(ValueError, match='must be str'):
                mock_business_logic.create_sphere(
                    cube_name="test_cube",
                    source_name="test_source_12345",
                    file_type="psql",
                    sql_params=TEST_SQL_PARAMS,
                    measures={
                        "measures_custom_list": [
                            {
                                "source_column": "latitude",
                                "measure_name": invalid_measure_name,
                            }
                        ]
                    },
                )

    def test_measures_custom_list_nullable_validation(self, mock_business_logic):
        """Тест валидации nullable в measures_custom_list (должен быть bool)"""
        invalid_nullable_values = ["true", "false", 1, 0, "yes", "no", None, []]
        for invalid_nullable in invalid_nullable_values:
            with pytest.raises(ValueError, match='must be bool'):
                mock_business_logic.create_sphere(
                    cube_name="test_cube",
                    source_name="test_source_12345",
                    file_type="psql",
                    sql_params=TEST_SQL_PARAMS,
                    measures={
                        "measures_custom_list": [
                            {
                                "source_column": "latitude",
                                "nullable": invalid_nullable,
                            }
                        ]
                    },
                )

    @pytest.mark.parametrize(
        "nullable_value",
        [True, False],
    )
    def test_measures_custom_list_nullable_valid_values(
        self, mock_business_logic, nullable_value
    ):
        """Тест валидных значений nullable в measures_custom_list"""
        mock_business_logic.create_sphere(
            cube_name="test_cube",
            source_name="test_source_12345",
            file_type="psql",
            sql_params=TEST_SQL_PARAMS,
            measures={
                "measures_list": ["latitude"],
                "measures_custom_list": [
                    {
                        "source_column": "latitude",
                        "nullable": nullable_value,
                    }
                ]
            },
        )

        # Проверяем, что в последнем вызове execute_manager_command переданы правильные facts
        last_call = mock_business_logic.execute_manager_command.call_args_list[-1]
        assert "facts" in last_call.kwargs
        assert len(last_call.kwargs["facts"]) == 1
        assert last_call.kwargs["facts"][0]["nulls_allowed"] == nullable_value

    def test_measures_custom_list_complete_example(self, mock_business_logic, mocker):
        """Тест полного примера использования measures_custom_list со всеми параметрами"""
        # Мокируем get_and_process_dims_and_measures
        expected_dims = [
            {"id": "dim1", "name": "date", "type": 6, "mark": 1, "field_id": "f1", "db_field": "date",
             "update_ts": 0, "datasource": "test_source", "field_type": "field"},
        ]
        expected_measures = [
            {"id": "m1", "name": "Широта", "mark": 1, "nulls_allowed": True, "field_id": "f2",
             "db_field": "latitude", "update_ts": 0, "datasource": "test_source", "field_type": "field"},
            {"id": "m2", "name": "Долгота", "mark": 1, "nulls_allowed": False, "field_id": "f3",
             "db_field": "longitude", "update_ts": 0, "datasource": "test_source", "field_type": "field"},
        ]
        mock_business_logic.h.get_and_process_dims_and_measures = mocker.Mock(
            return_value=(expected_dims, expected_measures)
        )

        mock_business_logic.create_sphere(
            cube_name="test_cube",
            source_name="test_source_12345",
            file_type="psql",
            sql_params=TEST_SQL_PARAMS,
            measures={
                "measures_custom_list": [
                    {
                        "source_column": "latitude",
                        "measure_name": "Широта",
                        "nullable": True,
                    },
                    {
                        "source_column": "longitude",
                        "measure_name": "Долгота",
                        "nullable": False,
                    },
                ]
            },
        )

        # Проверяем, что в последнем вызове execute_manager_command переданы правильные facts
        last_call = mock_business_logic.execute_manager_command.call_args_list[-1]
        assert "facts" in last_call.kwargs
        assert len(last_call.kwargs["facts"]) == 2
        measure_names = [m["name"] for m in last_call.kwargs["facts"]]
        assert "Широта" in measure_names
        assert "Долгота" in measure_names
        # Проверяем nullable значения
        for fact in last_call.kwargs["facts"]:
            if fact["name"] == "Широта":
                assert fact["nulls_allowed"] is True
            elif fact["name"] == "Долгота":
                assert fact["nulls_allowed"] is False

    def test_measures_combined_usage(self, mock_business_logic, mocker):
        """Тест комбинированного использования measures_list и measures_custom_list"""
        # Мокируем get_and_process_dims_and_measures
        expected_dims = [
            {"id": "dim1", "name": "date", "type": 6, "mark": 1, "field_id": "f1", "db_field": "date",
             "update_ts": 0, "datasource": "test_source", "field_type": "field"},
        ]
        expected_measures = [
            {"id": "m1", "name": "Широта", "mark": 1, "nulls_allowed": True, "field_id": "f2",
             "db_field": "latitude", "update_ts": 0, "datasource": "test_source", "field_type": "field"},
            {"id": "m2", "name": "longitude", "mark": 1, "nulls_allowed": False, "field_id": "f3",
             "db_field": "longitude", "update_ts": 0, "datasource": "test_source", "field_type": "field"},
        ]
        mock_business_logic.h.get_and_process_dims_and_measures = mocker.Mock(
            return_value=(expected_dims, expected_measures)
        )

        mock_business_logic.create_sphere(
            cube_name="test_cube",
            source_name="test_source_12345",
            file_type="psql",
            sql_params=TEST_SQL_PARAMS,
            measures={
                "measures_list_mode": "whitelist",
                "measures_list": ["latitude", "longitude"],
                "measures_custom_list": [
                    {
                        "source_column": "latitude",
                        "measure_name": "Широта",
                        "nullable": True,
                    }
                ],
            },
        )

        # Проверяем, что в последнем вызове execute_manager_command переданы правильные facts
        last_call = mock_business_logic.execute_manager_command.call_args_list[-1]
        assert "facts" in last_call.kwargs
        assert len(last_call.kwargs["facts"]) == 2
        measure_names = [m["name"] for m in last_call.kwargs["facts"]]
        assert "Широта" in measure_names
        assert "longitude" in measure_names
        # Проверяем, что для latitude применен кастомный measure_name и nullable
        for fact in last_call.kwargs["facts"]:
            if fact["name"] == "Широта":
                assert fact["nulls_allowed"] is True
