#!/usr/bin/python3
"""
Юнит-тесты для метода create_sphere_multisource из business_scenarios.py
"""

import pytest

from polymatica.business_scenarios import BusinessLogic
from polymatica.exceptions import PolymaticaException
from tests.const import TEST_SQL_PARAMS, TEST_SQL_PARAMS_JDBC


class TestCreateSphereMultisource:
    """Тесты для метода create_sphere_multisource"""

    @pytest.fixture
    def mock_business_logic(
        self, mocker, mock_server_codes, mock_config, mock_execute_manager_command_multisource_with_links
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
            side_effect=mock_execute_manager_command_multisource_with_links
        )
        bl.get_cubes_list = mocker.Mock(return_value=[])

        bl.h.upload_file_to_server = mocker.Mock(return_value="datasource_test_id")

        return bl

    def test_sources_minimum_count(self, mock_business_logic):
        """Тест валидации минимального количества источников (минимум 2)"""
        # Один источник - должна быть ошибка
        with pytest.raises(ValueError, match="For one source use create_sphere method"):
            mock_business_logic.create_sphere_multisource(
                cube_name="test_cube",
                sources=[
                    {
                        "source_name": "test_source_12345",
                        "file_type": "psql",
                        "sql_params": TEST_SQL_PARAMS,
                    }
                ],
            )

        # Два источника - должно работать
        mock_business_logic.create_sphere_multisource(
            cube_name="test_cube",
            sources=[
                {
                    "source_name": "test_source_12345",
                    "file_type": "psql",
                    "sql_params": TEST_SQL_PARAMS,
                },
                {
                    "source_name": "test_source_67890",
                    "file_type": "psql",
                    "sql_params": TEST_SQL_PARAMS,
                },
            ],
        )

    def test_sources_structure_validation(self, mock_business_logic):
        """Тест валидации структуры источников"""
        # Отсутствует source_name
        with pytest.raises(ValueError, match="must be specified"):
            mock_business_logic.create_sphere_multisource(
                cube_name="test_cube",
                sources=[
                    {
                        "file_type": "psql",
                        "sql_params": TEST_SQL_PARAMS,
                    },
                    {
                        "source_name": "test_source_67890",
                        "file_type": "psql",
                        "sql_params": TEST_SQL_PARAMS,
                    },
                ],
            )

        # Некорректное source_name
        for incorrect_source_name in ["123", "sou:rce"]:
            with pytest.raises(ValueError):
                mock_business_logic.create_sphere_multisource(
                    cube_name="test_cube",
                    sources=[
                        {
                            "source_name": incorrect_source_name,
                            "file_type": "psql",
                            "sql_params": TEST_SQL_PARAMS,
                        },
                        {
                            "source_name": "test_source_67890",
                            "file_type": "psql",
                            "sql_params": TEST_SQL_PARAMS,
                        },
                    ],
                )

        # Отсутствует file_type
        with pytest.raises(ValueError, match="must be specified"):
            mock_business_logic.create_sphere_multisource(
                cube_name="test_cube",
                sources=[
                    {
                        "source_name": "test_source_12345",
                        "sql_params": TEST_SQL_PARAMS,
                    },
                    {
                        "source_name": "test_source_67890",
                        "file_type": "psql",
                        "sql_params": TEST_SQL_PARAMS,
                    },
                ],
            )

        # Некорректный file_type
        for incorrect_file_type in ["file", ".csv"]:
            with pytest.raises(ValueError):
                mock_business_logic.create_sphere_multisource(
                    cube_name="test_cube",
                    sources=[
                        {
                            "source_name": "test_source_12345",
                            "file_type": incorrect_file_type,
                            "sql_params": TEST_SQL_PARAMS,
                        },
                        {
                            "source_name": "test_source_67890",
                            "file_type": "psql",
                            "sql_params": TEST_SQL_PARAMS,
                        },
                    ],
                )

    def test_links_basic_structure(self, mock_business_logic):
        """Тест базовой структуры связей между источниками"""
        sources = [
            {
                "source_name": "source1",
                "file_type": "psql",
                "sql_params": TEST_SQL_PARAMS,
            },
            {
                "source_name": "source2",
                "file_type": "psql",
                "sql_params": TEST_SQL_PARAMS,
            },
        ]

        links = [
            {
                "link_name": "link1",
                "source_name_1": "source1",
                "source_name_2": "source2",
                "column_1": "id",
                "column_2": "id1",
            }
        ]

        mock_business_logic.create_sphere_multisource(
            cube_name="test_cube", sources=sources, links=links
        )

        # Проверяем, что в последнем вызове execute_manager_command передан верный link1
        last_call = mock_business_logic.execute_manager_command.call_args_list[-1]
        assert last_call.kwargs["dims"][-1]["name"] == "link1"
        assert last_call.kwargs["facts"][-1]["name"] == "link1"

    def test_links_link_role_validation(self, mock_business_logic):
        """Тест валидации link_role в связях"""
        sources = [
            {
                "source_name": "source1",
                "file_type": "psql",
                "sql_params": TEST_SQL_PARAMS,
            },
            {
                "source_name": "source2",
                "file_type": "psql",
                "sql_params": TEST_SQL_PARAMS,
            },
        ]

        # Валидные значения link_role: 1, 2, 3
        for link_role in [1, 2, 3]:
            links = [
                {
                    "link_name": "link1",
                    "source_name_1": "source1",
                    "source_name_2": "source2",
                    "column_1": "id",
                    "column_2": "id1",
                    "link_role": link_role,
                }
            ]

            mock_business_logic.create_sphere_multisource(
                cube_name="test_cube", sources=sources, links=links
            )

    def test_measures_list_with_source_name(self, mock_business_logic, mocker):
        """Тест measures_list с указанием source_name"""
        sources = [
            {
                "source_name": "source1",
                "file_type": "psql",
                "sql_params": TEST_SQL_PARAMS,
            },
            {
                "source_name": "source2",
                "file_type": "psql",
                "sql_params": TEST_SQL_PARAMS,
            },
        ]

        # Мокируем get_and_process_dims_and_measures для multisource
        expected_dims = [
            {
                "id": "dim1",
                "name": "date",
                "type": 6,
                "mark": 1,
                "field_id": "f1",
                "db_field": "date",
                "update_ts": 0,
                "datasource": "source1",
                "field_type": "field",
            },
        ]
        expected_measures = [
            {
                "id": "m1",
                "name": "latitude",
                "mark": 1,
                "nulls_allowed": False,
                "field_id": "f2",
                "db_field": "latitude",
                "update_ts": 0,
                "datasource": "source1",
                "field_type": "field",
            },
            {
                "id": "m2",
                "name": "longitude",
                "mark": 1,
                "nulls_allowed": False,
                "field_id": "f3",
                "db_field": "longitude",
                "update_ts": 0,
                "datasource": "source2",
                "field_type": "field",
            },
        ]
        mock_business_logic.h.get_and_process_dims_and_measures = mocker.Mock(
            return_value=(expected_dims, expected_measures)
        )

        measures = {
            "measures_list_mode": "whitelist",
            "measures_list": [
                {"source_name": "source1", "measures": ["latitude"]},
                {"source_name": "source2", "measures": ["longitude"]},
            ],
        }

        mock_business_logic.create_sphere_multisource(
            cube_name="test_cube", sources=sources, measures=measures
        )

        # Проверяем, что в последнем вызове execute_manager_command переданы правильные facts
        last_call = mock_business_logic.execute_manager_command.call_args_list[-1]
        assert "facts" in last_call.kwargs
        assert len(last_call.kwargs["facts"]) == 2
        measure_names = [m["name"] for m in last_call.kwargs["facts"]]
        assert "latitude" in measure_names
        assert "longitude" in measure_names

    def test_measures_list_source_name_validation(self, mock_business_logic):
        """Тест валидации source_name в measures_list (должен существовать в sources)"""
        sources = [
            {
                "source_name": "source1",
                "file_type": "psql",
                "sql_params": TEST_SQL_PARAMS,
            },
            {
                "source_name": "source2",
                "file_type": "psql",
                "sql_params": TEST_SQL_PARAMS,
            },
        ]

        measures = {
            "measures_list_mode": "whitelist",
            "measures_list": [
                {"source_name": "nonexistent_source", "measures": ["latitude"]},
            ],
        }

        with pytest.raises((PolymaticaException, ValueError)):
            mock_business_logic.create_sphere_multisource(
                cube_name="test_cube", sources=sources, measures=measures
            )

    def test_measures_custom_list_with_source_name(self, mock_business_logic, mocker):
        """Тест measures_custom_list с указанием source_name"""
        sources = [
            {
                "source_name": "source1",
                "file_type": "psql",
                "sql_params": TEST_SQL_PARAMS,
            },
            {
                "source_name": "source2",
                "file_type": "psql",
                "sql_params": TEST_SQL_PARAMS,
            },
        ]

        # Мокируем get_and_process_dims_and_measures
        expected_dims = [
            {
                "id": "dim1",
                "name": "date",
                "type": 6,
                "mark": 1,
                "field_id": "f1",
                "db_field": "date",
                "update_ts": 0,
                "datasource": "source1",
                "field_type": "field",
            },
        ]
        expected_measures = [
            {
                "id": "m1",
                "name": "Широта",
                "mark": 1,
                "nulls_allowed": True,
                "field_id": "f2",
                "db_field": "latitude",
                "update_ts": 0,
                "datasource": "source1",
                "field_type": "field",
            },
            {
                "id": "m2",
                "name": "Долгота",
                "mark": 1,
                "nulls_allowed": False,
                "field_id": "f3",
                "db_field": "longitude",
                "update_ts": 0,
                "datasource": "source2",
                "field_type": "field",
            },
        ]
        mock_business_logic.h.get_and_process_dims_and_measures = mocker.Mock(
            return_value=(expected_dims, expected_measures)
        )

        measures = {
            "measures_custom_list": [
                {
                    "source_name": "source1",
                    "source_column": "latitude",
                    "measure_name": "Широта",
                    "nullable": True,
                },
                {
                    "source_name": "source2",
                    "source_column": "longitude",
                    "measure_name": "Долгота",
                    "nullable": False,
                },
            ],
        }

        mock_business_logic.create_sphere_multisource(
            cube_name="test_cube", sources=sources, measures=measures
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

    def test_measures_custom_list_source_name_validation(self, mock_business_logic):
        """Тест валидации source_name в measures_custom_list (должен существовать в sources)"""
        sources = [
            {
                "source_name": "source1",
                "file_type": "psql",
                "sql_params": TEST_SQL_PARAMS,
            },
            {
                "source_name": "source2",
                "file_type": "psql",
                "sql_params": TEST_SQL_PARAMS,
            },
        ]

        measures = {
            "measures_custom_list": [
                {
                    "source_name": "nonexistent_source",
                    "source_column": "latitude",
                    "measure_name": "Широта",
                },
            ],
        }

        with pytest.raises((PolymaticaException, ValueError)):
            mock_business_logic.create_sphere_multisource(
                cube_name="test_cube", sources=sources, measures=measures
            )

    def test_dims_list_with_source_name(self, mock_business_logic):
        """Тест dims_list с указанием source_name"""
        sources = [
            {
                "source_name": "source1",
                "file_type": "psql",
                "sql_params": TEST_SQL_PARAMS,
            },
            {
                "source_name": "source2",
                "file_type": "psql",
                "sql_params": TEST_SQL_PARAMS,
            },
        ]

        dims = {
            "dims_list_mode": "whitelist",
            "dims_list": [
                {"source_name": "source1", "dims": ["date"]},
                {"source_name": "source2", "dims": ["date4"]},
            ],
        }

        mock_business_logic.create_sphere_multisource(
            cube_name="test_cube", sources=sources, dims=dims
        )

        # Проверяем, что в последнем вызове execute_manager_command переданы правильные dims
        last_call = mock_business_logic.execute_manager_command.call_args_list[-1]
        assert "dims" in last_call.kwargs
        dim_names = [d["name"] for d in last_call.kwargs["dims"]]
        assert "date" in dim_names
        assert "date4" in dim_names

    def test_dims_list_source_name_validation(self, mock_business_logic):
        """Тест валидации source_name в dims_list (должен существовать в sources)"""
        sources = [
            {
                "source_name": "source1",
                "file_type": "psql",
                "sql_params": TEST_SQL_PARAMS,
            },
            {
                "source_name": "source2",
                "file_type": "psql",
                "sql_params": TEST_SQL_PARAMS,
            },
        ]

        dims = {
            "dims_list_mode": "whitelist",
            "dims_list": [
                {"source_name": "nonexistent_source", "dims": ["date"]},
            ],
        }

        with pytest.raises((PolymaticaException, ValueError)):
            mock_business_logic.create_sphere_multisource(
                cube_name="test_cube", sources=sources, dims=dims
            )

    def test_dims_custom_list_with_source_name(self, mock_business_logic):
        """Тест dims_custom_list с указанием source_name"""
        sources = [
            {
                "source_name": "source1",
                "file_type": "psql",
                "sql_params": TEST_SQL_PARAMS,
            },
            {
                "source_name": "source2",
                "file_type": "psql",
                "sql_params": TEST_SQL_PARAMS,
            },
        ]

        dims = {
            "dims_custom_list": [
                {
                    "source_name": "source1",
                    "source_column": "date",
                    "dim_name": "Дата",
                    "date_details": ["year", "month"],
                },
                {
                    "source_name": "source2",
                    "source_column": "date4",
                    "dim_name": "ДатаВремя",
                    "date_details": ["date", "year", "quarter"],
                },
            ],
        }

        mock_business_logic.create_sphere_multisource(
            cube_name="test_cube", sources=sources, dims=dims
        )

        # Проверяем, что в последнем вызове execute_manager_command переданы правильные dims
        last_call = mock_business_logic.execute_manager_command.call_args_list[-1]
        assert "dims" in last_call.kwargs
        dim_names = [d["name"] for d in last_call.kwargs["dims"]]
        assert "Дата" in dim_names
        assert "ДатаВремя" in dim_names

    def test_dims_custom_list_source_name_validation(self, mock_business_logic):
        """Тест валидации source_name в dims_custom_list (должен существовать в sources)"""
        sources = [
            {
                "source_name": "source1",
                "file_type": "psql",
                "sql_params": TEST_SQL_PARAMS,
            },
            {
                "source_name": "source2",
                "file_type": "psql",
                "sql_params": TEST_SQL_PARAMS,
            },
        ]

        dims = {
            "dims_custom_list": [
                {
                    "source_name": "nonexistent_source",
                    "source_column": "date",
                    "dim_name": "Дата",
                },
            ],
        }

        with pytest.raises((PolymaticaException, ValueError)):
            mock_business_logic.create_sphere_multisource(
                cube_name="test_cube", sources=sources, dims=dims
            )

    def test_combined_measures_and_dims_with_sources(self, mock_business_logic, mocker):
        """Тест комбинированного использования measures и dims с указанием source_name"""
        sources = [
            {
                "source_name": "source1",
                "file_type": "psql",
                "sql_params": TEST_SQL_PARAMS,
            },
            {
                "source_name": "source2",
                "file_type": "psql",
                "sql_params": TEST_SQL_PARAMS,
            },
        ]

        # Мокируем get_and_process_dims_and_measures
        expected_dims = [
            {
                "id": "dim1",
                "name": "Дата",
                "type": 6,
                "mark": 1,
                "field_id": "f1",
                "db_field": "date",
                "update_ts": 0,
                "datasource": "source1",
                "field_type": "field",
            },
        ]
        expected_measures = [
            {
                "id": "m1",
                "name": "Широта",
                "mark": 1,
                "nulls_allowed": True,
                "field_id": "f2",
                "db_field": "latitude",
                "update_ts": 0,
                "datasource": "source1",
                "field_type": "field",
            },
        ]
        mock_business_logic.h.get_and_process_dims_and_measures = mocker.Mock(
            return_value=(expected_dims, expected_measures)
        )

        measures = {
            "measures_list_mode": "whitelist",
            "measures_list": [
                {"source_name": "source1", "measures": ["latitude"]},
            ],
            "measures_custom_list": [
                {
                    "source_name": "source1",
                    "source_column": "latitude",
                    "measure_name": "Широта",
                    "nullable": True,
                },
            ],
        }

        dims = {
            "dims_list_mode": "whitelist",
            "dims_list": [
                {"source_name": "source1", "dims": ["date"]},
            ],
            "dims_custom_list": [
                {
                    "source_name": "source1",
                    "source_column": "date",
                    "dim_name": "Дата",
                    "date_details": ["year", "month"],
                },
            ],
        }

        mock_business_logic.create_sphere_multisource(
            cube_name="test_cube", sources=sources, measures=measures, dims=dims
        )

        # Проверяем, что в последнем вызове execute_manager_command переданы правильные данные
        last_call = mock_business_logic.execute_manager_command.call_args_list[-1]
        assert "dims" in last_call.kwargs
        assert "facts" in last_call.kwargs
        dim_names = [d["name"] for d in last_call.kwargs["dims"]]
        measure_names = [m["name"] for m in last_call.kwargs["facts"]]
        assert "Дата" in dim_names
        assert "Широта" in measure_names
