# Fork 自定义说明 (Custom Fork Notes)

> 本文件记录本仓库相对上游 [richonguzman/LoRa_APRS_iGate](https://github.com/richonguzman/LoRa_APRS_iGate) 的自定义修改。
> `README.md` 保持与上游同步不做改动,所有自定义内容集中记录在此,避免 Sync Fork 时产生冲突。

____________________________________________________

## 目标板型

**ESP32-C3 + Ebyte E22-400M30S(1W LoRa 模块)DIY 版本**(`esp32c3_DIY_1W_LoRa`)

上游该变体的默认引脚不适配我实际接线方式,因此新增自定义引脚补丁,详见下方。

____________________________________________________

## 1. 自定义引脚配置

新增脚本:[`apply_custom_pins.py`](./apply_custom_pins.py)(仓库根目录,上游没有此文件)

**作用**:在 CI 构建时,动态修改 `variants/esp32c3_DIY_1W_LoRa/board_pinout.h` 中的引脚宏定义,匹配实际接线:

| 功能 | 引脚 |
|---|---|
| SCLK | GPIO 10 |
| MISO | GPIO 6 |
| MOSI | GPIO 7 |
| CS | GPIO 8 |
| RST | GPIO 5 |
| DIO1 | GPIO 3 |
| BUSY | GPIO 4 |
| RXEN | GPIO 2 |
| TXEN | 未使用 (`GPIO_NUM_NC`) |
| WAKEUP | GPIO 3 |

**重要机制**:该脚本只在**构建时**临时修改工作目录里的文件,**不会 commit 回仓库**。仓库里的 `board_pinout.h` 内容始终与上游保持一致 → Sync Fork 时这个文件不会冲突。

**已知风险**:脚本靠正则精确匹配文本,如果上游改动了这个文件里的变量名/格式,补丁可能**静默失败**(不报错,但也没生效)。→ 见下方「维护流程」第 2 步。

____________________________________________________

## 2. GitHub Actions 工作流

仓库 `.github/workflows/` 下维护两个流程(均为新增,上游没有):

### `Commit Test Build`(CI 测试)
- **触发**:push 到任意分支
- **作用**:同时编译 `ttgo-lora32-v21` 和 `esp32c3_DIY_1W_LoRa`,验证代码/补丁能否正常构建,不发布,仅上传 Artifact(保留 30 天)

### `Release esp32c3_DIY_1W_LoRa Firmware`(正式发布)
- **触发**:发布 GitHub Release,或手动 `workflow_dispatch`
- **流程**:
  1. 应用自定义引脚补丁
  2. 编译 `esp32c3_DIY_1W_LoRa` 固件
  3. 从上游最新 Release 下载官方 `spiffs.bin`(WebUI 静态资源,直接复用)
  4. 用 `esptool.py merge_bin` 合并 bootloader + 分区表 + boot_app0 + firmware + spiffs → 生成一键烧录的 **`factory.bin`**
  5. 上传 `factory.bin` / `firmware.bin` / `spiffs.bin` 到 Release 页面 + Artifacts(保留 90 天)

____________________________________________________

## 3. 日常维护流程(上游更新时)

1. **Sync Fork**:GitHub 仓库页面点击 "Sync fork" → "Update branch",拉取上游最新代码
   - `apply_custom_pins.py`、workflow 文件、本文件均不受影响(上游没有同名文件)
   - `README.md` 也不会冲突(本仓库未修改它)
2. **自动验证**:Sync 完成会自动触发 `Commit Test Build`,查看运行结果:
   - 编译是否成功
   - 重点检查日志中 "Verify patched pins" 步骤的输出,确认 10 个引脚确实被正确替换(不能只看流程是否显示绿色✅)
3. **手动发布**:确认无误后,手动触发 `Release esp32c3_DIY_1W_LoRa Firmware`(Actions 页面 → Run workflow),生成并发布新固件

____________________________________________________

## 4. 如果 `apply_custom_pins.py` 匹配失败怎么办

现象:CI 运行显示成功,但 "Verify patched pins" 打印出的引脚**没有变化**(还是上游默认值)。

原因:上游改了 `board_pinout.h` 里对应宏定义的写法(变量名、空格、注释位置等),导致脚本里的正则匹配不上。

处理:对照 CI 日志打印出的最新 `board_pinout.h` 内容,手动更新 `apply_custom_pins.py` 里对应的正则表达式,使其能匹配新格式。

____________________________________________________

*最后更新维护说明日期:2026-09*
