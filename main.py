"""In-memory idempotency keys bound to request bytes, with cached byte responses."""
import argparse
from dataclasses import dataclass
import hashlib
import json
import math
import threading


