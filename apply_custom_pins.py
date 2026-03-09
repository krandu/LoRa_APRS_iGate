#!/usr/bin/env python3
"""
Custom pin config for ESP32-C3 DIY board with E22-400M30S
Replaces cr2rxu default pins with custom SPI wiring
"""

import re

# ── 1. board_pinout.h ──────────────────────────────────────────────
PINOUT_FILE = "variants/esp32c3_DIY_1W_LoRa/board_pinout.h"

PIN_MAP = {
    r"(#define RADIO_SCLK_PIN\s+)\d+":  r"\g<1>10",
    r"(#define RADIO_MISO_PIN\s+)\d+":  r"\g<1>6",
    r"(#define RADIO_MOSI_PIN\s+)\d+":  r"\g<1>7",
    r"(#define RADIO_CS_PIN\s+)\d+":    r"\g<1>8",
    r"(#define RADIO_RST_PIN\s+)\d+":   r"\g<1>5",
    r"(#define RADIO_DIO1_PIN\s+)\d+":  r"\g<1>3",
    r"(#define RADIO_BUSY_PIN\s+)\d+":  r"\g<1>4",
    r"(#define RADIO_RXEN\s+)\d+":      r"\g<1>2",
    r"(#define RADIO_TXEN\s+)\d+":      r"\g<1>GPIO_NUM_NC",
    r"(#define GPIO_WAKEUP_PIN\s+)GPIO_NUM_\d+": r"\g<1>GPIO_NUM_3",
}

with open(PINOUT_FILE, "r") as f:
    content = f.read()

for pattern, replacement in PIN_MAP.items():
    content = re.sub(pattern, replacement, content)

with open(PINOUT_FILE, "w") as f:
    f.write(content)

print(f"[OK] {PINOUT_FILE} pins updated")

# ── 2. lora_utils.cpp ─────────────────────────────────────────────
LORA_FILE = "src/lora_utils.cpp"

with open(LORA_FILE, "r") as f:
    content = f.read()

# 替换 SX1268 radio 声明：移除 LIGHTGATEWAY 条件分支，统一用 loraSPI
OLD_SX1268 = """\
#ifdef HAS_SX1268
    #if defined(LIGHTGATEWAY_1_0) || defined(LIGHTGATEWAY_PLUS_1_0)
        SPIClass loraSPI(FSPI);
        SX1268 radio = new Module(RADIO_CS_PIN, RADIO_DIO1_PIN, RADIO_RST_PIN, RADIO_BUSY_PIN, loraSPI);
    #else
        SX1268 radio = new Module(RADIO_CS_PIN, RADIO_DIO1_PIN, RADIO_RST_PIN, RADIO_BUSY_PIN);
    #endif
#endif"""

NEW_SX1268 = """\
#ifdef HAS_SX1268
    SPIClass loraSPI(FSPI);
    SX1268 radio = new Module(RADIO_CS_PIN, RADIO_DIO1_PIN, RADIO_RST_PIN, RADIO_BUSY_PIN, loraSPI);
#endif"""

# 替换 SPI.begin 初始化块
OLD_SPI = """\
        #if defined (LIGHTGATEWAY_1_0) || defined(LIGHTGATEWAY_PLUS_1_0)
            pinMode(RADIO_VCC_PIN,OUTPUT);
            digitalWrite(RADIO_VCC_PIN,HIGH);
            loraSPI.begin(RADIO_SCLK_PIN, RADIO_MISO_PIN, RADIO_MOSI_PIN, RADIO_CS_PIN);
        #else
            SPI.begin(RADIO_SCLK_PIN, RADIO_MISO_PIN, RADIO_MOSI_PIN);
        #endif"""

NEW_SPI = """\
        #if defined (LIGHTGATEWAY_1_0) || defined(LIGHTGATEWAY_PLUS_1_0)
            pinMode(RADIO_VCC_PIN,OUTPUT);
            digitalWrite(RADIO_VCC_PIN,HIGH);
        #endif
        loraSPI.begin(RADIO_SCLK_PIN, RADIO_MISO_PIN, RADIO_MOSI_PIN, RADIO_CS_PIN);"""

if OLD_SX1268 in content:
    content = content.replace(OLD_SX1268, NEW_SX1268)
    print("[OK] lora_utils.cpp SX1268 declaration updated")
else:
    print("[WARN] SX1268 block not found - already patched or source changed?")

if OLD_SPI in content:
    content = content.replace(OLD_SPI, NEW_SPI)
    print("[OK] lora_utils.cpp SPI init updated")
else:
    print("[WARN] SPI init block not found - already patched or source changed?")

with open(LORA_FILE, "w") as f:
    f.write(content)

print("Done.")
