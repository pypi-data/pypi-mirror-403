"""Delete WordLift entities from CSV."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from typing import List

import requests
from tqdm import tqdm

from worai.core.wordlift import DEFAULT_ENTITIES_ENDPOINT

BATCH_SIZE = 10


@dataclass
class DeleteEntitiesOptions:
    api_key: str
    csv_file: str
    batch_size: int = BATCH_SIZE


def _read_iris(csv_file: str) -> List[str]:
    with open(csv_file, newline="", encoding="utf-8") as f:
        reader = list(csv.reader(f))
    return [row[0].strip() for row in reader if row and row[0].strip()]


def delete_entities(options: DeleteEntitiesOptions) -> None:
    headers = {"Authorization": f"Key {options.api_key}"}
    iris = _read_iris(options.csv_file)

    for i in tqdm(range(0, len(iris), options.batch_size), desc="Deleting entities", unit="batch"):
        batch = iris[i : i + options.batch_size]
        params = "&".join([f"id={iri}" for iri in batch])
        url = f"{DEFAULT_ENTITIES_ENDPOINT}?{params}&include_children=true"
        response = requests.delete(url, headers=headers)

        if response.status_code == 200:
            tqdm.write(f"Successfully deleted batch: {', '.join(batch)}")
        else:
            tqdm.write(
                f"Failed to delete batch {', '.join(batch)}: {response.status_code} - {response.text}"
            )
