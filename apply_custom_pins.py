#!/usr/bin/env python3
"""
Custom pin config for ESP32-C3 DIY board with E22-400M30S
Only modifies board_pinout.h pin definitions
"""

import re

PINOUT_FILE = "variants/esp32c3_DIY_1W_LoRa/board_pinout.h"

PIN_MAP = {
    r"(#define RADIO_SCLK_PIN\s+)\d+":           r"\g<1>10",
    r"(#define RADIO_MISO_PIN\s+)\d+":           r"\g<1>6",
    r"(#define RADIO_MOSI_PIN\s+)\d+":           r"\g<1>7",
    r"(#define RADIO_CS_PIN\s+)\d+":             r"\g<1>8",
    r"(#define RADIO_RST_PIN\s+)\d+":            r"\g<1>5",
    r"(#define RADIO_DIO1_PIN\s+)\d+":           r"\g<1>3",
    r"(#define RADIO_BUSY_PIN\s+)\d+":           r"\g<1>4",
    r"(#define RADIO_RXEN\s+)\d+":               r"\g<1>2",
    r"(#define RADIO_TXEN\s+)\d+":               r"\g<1>GPIO_NUM_NC",
    r"(#define GPIO_WAKEUP_PIN\s+)GPIO_NUM_\d+": r"\g<1>GPIO_NUM_3",
}

with open(PINOUT_FILE, "r") as f:
    content = f.read()

for pattern, replacement in PIN_MAP.items():
    content = re.sub(pattern, replacement, content)

with open(PINOUT_FILE, "w") as f:
    f.write(content)

print(f"[OK] {PINOUT_FILE} pins updated")
print("Done.")
