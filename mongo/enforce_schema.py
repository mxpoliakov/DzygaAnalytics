from common.config import get_collection_name
from common.config import get_sources_names_list
from common.mongo import get_database


def enforce_schema(collection=get_collection_name(), sources=get_sources_names_list()):
    db = get_database()
    validator = {
        "$jsonSchema": {
            "bsonType": "object",
            "required": [
                "senderName",
                "senderEmail",
                "datetime",
                "currency",
                "donationSource",
                "amountUSD",
                "amountOriginal",
                "senderNote",
                "insertionMode",
            ],
            "properties": {
                "senderName": {
                    "bsonType": ["string", "null"],
                    "description": "must be a string or null and is required",
                },
                "senderEmail": {
                    "bsonType": ["string", "null"],
                    "description": "must be a string or null and is required",
                },
                "currency": {
                    "bsonType": ["string"],
                    "description": "must be a string is required",
                },
                "senderNote": {
                    "bsonType": ["string"],
                    "description": "must be a string is required",
                },
                "donationSource": {
                    "enum": sources,
                    "description": "can only be one of the enum values and is required",
                },
                "insertionMode": {
                    "enum": ["Manual", "Auto"],
                    "description": "can only be one of the enum values and is required",
                },
                "amountUSD": {
                    "bsonType": ["double"],
                    "minimum": 0,
                    "description": "must be a double and is required",
                },
                "amountOriginal": {
                    "bsonType": ["double"],
                    "minimum": 0,
                    "description": "must be a double and is required",
                },
            },
        }
    }

    db.command("collMod", collection, validator=validator, validationLevel="strict")


if __name__ == "__main__":
    enforce_schema()
