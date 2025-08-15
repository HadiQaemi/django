from hashids import Hashids
from django.conf import settings
from typing import Optional, Union
import logging

logger = logging.getLogger(__name__)


class IDEncoder:
    """Utility class for encoding/decoding IDs"""

    def __init__(self):
        # Use a secret salt from settings
        salt = getattr(settings, "HASHID_SALT", "reborn-api-default-salt-change-me")
        # Minimum length for encoded IDs
        min_length = getattr(settings, "HASHID_MIN_LENGTH", 8)
        # Custom alphabet (optional)
        alphabet = getattr(
            settings, "HASHID_ALPHABET", "abcdefghijklmnopqrstuvwxyz1234567890"
        )

        self.hashids = Hashids(salt=salt, min_length=min_length, alphabet=alphabet)

    def encode_id(self, id_value: Union[int, str]) -> Optional[str]:
        try:
            if isinstance(id_value, str):
                # Try to convert string to int
                id_value = int(id_value)

            if not isinstance(id_value, int) or id_value <= 0:
                logger.warning(f"Invalid ID for encoding: {id_value}")
                return None

            encoded = self.hashids.encode(id_value)
            logger.debug(f"Encoded ID {id_value} to {encoded}")
            return encoded

        except (ValueError, TypeError) as e:
            logger.error(f"Error encoding ID {id_value}: {str(e)}")
            return None

    def decode_id(self, encoded_id: str) -> Optional[int]:
        try:
            if not encoded_id or not isinstance(encoded_id, str):
                logger.warning(f"Invalid encoded ID: {encoded_id}")
                return None

            decoded = self.hashids.decode(encoded_id)

            if not decoded:
                logger.warning(f"Could not decode ID: {encoded_id}")
                return None

            # Return the first (and should be only) decoded ID
            original_id = decoded[0]
            logger.debug(f"Decoded {encoded_id} to ID {original_id}")
            return original_id

        except Exception as e:
            logger.error(f"Error decoding ID {encoded_id}: {str(e)}")
            return None

    def encode_multiple(self, *ids) -> Optional[str]:
        try:
            int_ids = []
            for id_val in ids:
                if isinstance(id_val, str):
                    int_ids.append(int(id_val))
                else:
                    int_ids.append(id_val)

            encoded = self.hashids.encode(*int_ids)
            logger.debug(f"Encoded multiple IDs {int_ids} to {encoded}")
            return encoded

        except (ValueError, TypeError) as e:
            logger.error(f"Error encoding multiple IDs {ids}: {str(e)}")
            return None

    def decode_multiple(self, encoded_id: str) -> Optional[tuple]:
        try:
            decoded = self.hashids.decode(encoded_id)

            if not decoded:
                logger.warning(f"Could not decode multiple IDs: {encoded_id}")
                return None

            logger.debug(f"Decoded {encoded_id} to IDs {decoded}")
            return tuple(decoded)

        except Exception as e:
            logger.error(f"Error decoding multiple IDs {encoded_id}: {str(e)}")
            return None


id_encoder = IDEncoder()


def encode_id(paper_id: Union[int, str]) -> Optional[str]:
    """Encode a paper ID"""
    return id_encoder.encode_id(paper_id)


def decode_paper_id(encoded_id: str) -> Optional[int]:
    """Decode a paper ID"""
    return id_encoder.decode_id(encoded_id)


def decode_id(encoded_id: str) -> Optional[int]:
    """Decode a paper ID"""
    return id_encoder.decode_id(encoded_id)
