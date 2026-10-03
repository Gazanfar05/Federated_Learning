from __future__ import annotations

import pandas as pd

from client.training.dataset import EXPECTED_COLUMNS, load_hospital1_csv


def test_dataset_loads_and_has_expected_columns():
    df = load_hospital1_csv()
    assert isinstance(df, pd.DataFrame)
    assert list(df.columns) == EXPECTED_COLUMNS
    assert 'Outcome' in df.columns


def test_no_patient_rows_in_payload_contract():
    payload = {'client_id': 'hospital_01', 'round_id': 1, 'protected_update': {'weights': [0.1, 0.2]}}
    assert 'Outcome' not in str(payload)
    assert 'Pregnancies' not in str(payload)
