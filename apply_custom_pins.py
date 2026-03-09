#!/usr/bin/env python3
"""
Custom pin config for ESP32-C3 DIY board with E22-400M30S
Replaces cr2rxu default pins with custom SPI wiring
Fixes:
  1. SPI init: use SPIClass loraSPI(FSPI) instead of global SPI
  2. TCXO init: move setTCXO() before radio.begin()
  3. RfSwitch: move setRfSwitchPins() before radio.begin()
"""

import re

# ── 1. board_pinout.h ──────────────────────────────────────────────
PINOUT_FILE = "variants/esp32c3_DIY_1W_LoRa/board_pinout.h"

PIN_MAP = {
    r"(#define RADIO_SCLK_PIN\s+)\d+":          r"\g<1>10",
    r"(#define RADIO_MISO_PIN\s+)\d+":          r"\g<1>6",
    r"(#define RADIO_MOSI_PIN\s+)\d+":          r"\g<1>7",
    r"(#define RADIO_CS_PIN\s+)\d+":            r"\g<1>8",
    r"(#define RADIO_RST_PIN\s+)\d+":           r"\g<1>5",
    r"(#define RADIO_DIO1_PIN\s+)\d+":          r"\g<1>3",
    r"(#define RADIO_BUSY_PIN\s+)\d+":          r"\g<1>4",
    r"(#define RADIO_RXEN\s+)\d+":              r"\g<1>7",
    r"(#define RADIO_TXEN\s+)\d+":              r"\g<1>GPIO_NUM_NC",
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

# ── 2a. SX1268 radio 声明：统一用 loraSPI ─────────────────────────
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

if OLD_SX1268 in content:
    content = content.replace(OLD_SX1268, NEW_SX1268)
    print("[OK] lora_utils.cpp SX1268 declaration updated")
else:
    print("[WARN] SX1268 block not found - already patched or source changed?")

# ── 2b. SPI.begin：改用 loraSPI.begin ─────────────────────────────
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

if OLD_SPI in content:
    content = content.replace(OLD_SPI, NEW_SPI)
    print("[OK] lora_utils.cpp SPI init updated")
else:
    print("[WARN] SPI init block not found - already patched or source changed?")

# ── 2c. 把 setTCXO 和 setRfSwitchPins 移到 radio.begin() 之前 ────
OLD_BEGIN_BLOCK = """\
        int state = radio.begin(freq);
        if (state != RADIOLIB_ERR_NONE) {
            Utils::println("Starting LoRa failed! State: " + String(state));
            while (true);
        }
        #if defined(HAS_SX1262) || defined(HAS_SX1268) || defined(HAS_LLCC68)
            radio.setDio1Action(setFlag);
        #endif
        #if defined(HAS_SX1278) || defined(HAS_SX1276)
            radio.setDio0Action(setFlag, RISING);
        #endif

        /*#ifdef SX126X_DIO3_TCXO_VOLTAGE
            if (radio.setTCXO(float(SX126X_DIO3_TCXO_VOLTAGE)) == RADIOLIB_ERR_NONE) {
                Utils::println("Set LoRa Module TCXO Voltage to:" + String(SX126X_DIO3_TCXO_VOLTAGE));
            } else {
                Utils::println("Set LoRa Module TCXO Voltage failed! State: " + String(state));
                while (true);
        }
         #endif*/

        radio.setSpreadingFactor(Config.loramodule.rxSpreadingFactor);
        radio.setCodingRate(Config.loramodule.rxCodingRate4);
        float signalBandwidth = Config.loramodule.rxSignalBandwidth / 1000;
        radio.setBandwidth(signalBandwidth);
        radio.setCRC(true);

        #if (defined(RADIO_RXEN) && defined(RADIO_TXEN))    // QRP Labs LightGateway has 400M22S (SX1268)
            radio.setRfSwitchPins(RADIO_RXEN, RADIO_TXEN);
        #endif"""

NEW_BEGIN_BLOCK = """\
        #ifdef HAS_TCXO
            radio.setTCXO(1.8);
        #endif
        #if (defined(RADIO_RXEN) && defined(RADIO_TXEN))
            radio.setRfSwitchPins(RADIO_RXEN, RADIO_TXEN);
        #endif

        int state = radio.begin(freq);
        if (state != RADIOLIB_ERR_NONE) {
            Utils::println("Starting LoRa failed! State: " + String(state));
            while (true);
        }
        #if defined(HAS_SX1262) || defined(HAS_SX1268) || defined(HAS_LLCC68)
            radio.setDio1Action(setFlag);
        #endif
        #if defined(HAS_SX1278) || defined(HAS_SX1276)
            radio.setDio0Action(setFlag, RISING);
        #endif

        /*#ifdef SX126X_DIO3_TCXO_VOLTAGE
            if (radio.setTCXO(float(SX126X_DIO3_TCXO_VOLTAGE)) == RADIOLIB_ERR_NONE) {
                Utils::println("Set LoRa Module TCXO Voltage to:" + String(SX126X_DIO3_TCXO_VOLTAGE));
            } else {
                Utils::println("Set LoRa Module TCXO Voltage failed! State: " + String(state));
                while (true);
        }
         #endif*/

        radio.setSpreadingFactor(Config.loramodule.rxSpreadingFactor);
        radio.setCodingRate(Config.loramodule.rxCodingRate4);
        float signalBandwidth = Config.loramodule.rxSignalBandwidth / 1000;
        radio.setBandwidth(signalBandwidth);
        radio.setCRC(true);

        #if (defined(RADIO_RXEN) && defined(RADIO_TXEN))    // QRP Labs LightGateway has 400M22S (SX1268)
            radio.setRfSwitchPins(RADIO_RXEN, RADIO_TXEN);
        #endif"""

if OLD_BEGIN_BLOCK in content:
    content = content.replace(OLD_BEGIN_BLOCK, NEW_BEGIN_BLOCK)
    print("[OK] lora_utils.cpp TCXO + RfSwitch moved before radio.begin()")
else:
    print("[WARN] begin block not found - already patched or source changed?")

with open(LORA_FILE, "w") as f:
    f.write(content)

print("Done.")
