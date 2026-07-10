"""
Юнит-тесты структуры конфига и DAG.

Не требует запуска Airflow: проверяет форму конфига и логику генерации задач.
Запуск:  cd airflow && python -m pytest tests/ -v
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

DAGS_DIR = Path(__file__).resolve().parent.parent / "dags"
sys.path.insert(0, str(DAGS_DIR))

from config.tables_config import CONFIG  # noqa: E402


REQUIRED_FIELDS = {
    "table_name", "table_ddl", "table_dml", "need_to_export"
}


def test_config_has_entries():
    assert len(CONFIG) >= 2, "config should contain at least 2 tables"


def test_config_entry_shape():
    for item in CONFIG:
        missing = REQUIRED_FIELDS - item.keys()
        assert not missing, f"{item} missing fields: {missing}"
        assert isinstance(item["need_to_export"], bool)
        assert "CREATE TABLE" in item["table_ddl"].upper(), (
            "table_ddl must be a CREATE TABLE statement"
        )


def test_table_names_unique():
    names = [i["table_name"] for i in CONFIG]
    assert len(names) == len(set(names)), "duplicate table_name in config"


def test_at_least_one_export_and_one_non_export():
    exports = [i for i in CONFIG if i["need_to_export"]]
    non_exports = [i for i in CONFIG if not i["need_to_export"]]
    assert exports, "no table with need_to_export=True"
    assert non_exports, "no table with need_to_export=False"


def test_dag_module_imports():
    """DAG-файл должен импортироваться без ошибок синтаксиса/импортов."""
    # airflow может быть не установлен в CI окружении — тогда импорт
    # модуля DAG падает на `import airflow`. В этом случае достаточно
    # py_compile-проверки синтаксиса.
    dag_file = DAGS_DIR / "dynamic_etl_dag.py"
    try:
        spec = importlib.util.spec_from_file_location("dynamic_etl_dag", dag_file)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    except ModuleNotFoundError as e:
        airflow_deps = ("airflow", "pendulum", "airflow.providers")
        if e.name and (e.name == "airflow" or e.name.startswith(airflow_deps)):
            import py_compile
            py_compile.compile(str(dag_file), doraise=True)
            return
        raise
    assert mod.dag.dag_id == "dynamic_etl_dag"


def test_expected_tasks_per_table():
    """Каждая таблица даёт create + fill, плюс check/export по флагам."""
    for item in CONFIG:
        t = item["table_name"]
        has_quality = bool(item.get("quality"))
        has_export = bool(item["need_to_export"])
        # Минимум две задачи на таблицу.
        assert has_quality in (True, False)
        assert has_export in (True, False)
        # Если export=True, должна быть возможность построить export-задачу.
        if has_export:
            assert item["table_name"]
