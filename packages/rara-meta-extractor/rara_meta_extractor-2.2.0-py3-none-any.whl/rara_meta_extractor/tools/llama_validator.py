import regex as re

from rara_meta_extractor.config import (
    LOGGER, FIELDS_TO_VALIDATE
)
from rara_meta_extractor.constants.data_classes import MetaField
from copy import deepcopy
from typing import List

class LlamaValidator:
    def __init__(self, fields_to_validate: List[str] = FIELDS_TO_VALIDATE):
        self.fields_to_validate: List[str] = self._format_fields(fields_to_validate)

    def _format_fields(self, fields: List[str]) -> List[str]:
        """ Make sure that all field names contain "_" instead of " " as word separators.
        """
        new_fields = []
        for field in fields:
            tokens = field.split()
            new_field = "_".join(tokens)
            new_fields.append(new_field)
        return new_fields


    def filter_false_positives(self, text: str, llama_output: dict):
        LOGGER.info(f"Filtering Llama output: {llama_output}")
        filtered_output = deepcopy(llama_output)
        text = text.lower()
        for field in self.fields_to_validate:
            LOGGER.debug(f"Valdating content for field '{field}'...")
            if field == MetaField.AUTHORS:
                key = "name"
            elif field == MetaField.TITLES:
                key = "title"

            values = llama_output.get(field, [])
            if not values:
                LOGGER.debug(f"Values for field '{field}' are not detected with Llama-Extractor or have already been filtered out.")
            if isinstance(values, str):
                val_value = values
                tokens = [re.escape(t.strip()) for t in val_value.lower().split() if t.strip()]
                search_value = r"\s*".join(tokens)
                if re.search(search_value, text):
                    filtered_output[field] = val_value
                    LOGGER.debug(f"Detected value '{val_value}' (field={field}) from the original text. Keeping it!")

                else:
                    filtered_output.pop(field, "")
                    LOGGER.debug(
                        f"Could not detect {field.upper()} value '{val_value}' from the original text. " \
                        f"Removing it from the output."
                    )

            elif isinstance(values, list):
                filtered_list = []
                for value in values:
                    val_value = ""
                    if isinstance(value, dict):
                        val_value = value.get(key)
                    elif isinstance(value, str):
                        val_value = value
                    if val_value:
                        tokens = [re.escape(t.strip()) for t in val_value.lower().split() if t.strip()]
                        search_value = r"\s*".join(tokens)
                        if re.search(search_value, text):
                            filtered_list.append(value)
                            LOGGER.debug(f"Detected value '{val_value}' (field={field}) from the original text. Keeping it!")
                        else:
                            LOGGER.debug(
                                f"Could not detect {field.upper()} value '{val_value}' from the original text. " \
                                f"Removing it from the output."
                            )
                if filtered_list:
                    filtered_output[field] = filtered_list
                else:
                    filtered_output.pop(field, "")
            else:
                LOGGER.debug(f"Values have unexpected type: {type(values)}.")

        LOGGER.info(f"Final filtered Llama-Extractor output: {filtered_output}")
        return filtered_output
