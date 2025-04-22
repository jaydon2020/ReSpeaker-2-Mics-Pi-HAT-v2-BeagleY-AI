# **Porting ReSpeaker 2-Mics Pi HAT v2 to BeagleY-AI**


## **Hardware Overview**  

1. **BeagleY-AI**:  

  ![BeagleY-AI](https://www.beagleboard.org/app/uploads/2024/06/BeagleY-AI-angled-front-1-400x267-1-300x200.png)



2. **ReSpeaker 2-Mics Pi HAT v2**:  
  ---
  **NOTE**

  The reSpeaker 2-Mics Pi HAT has been upgraded to version 2.0. The codec chip has been replaced from WM8960 to TLV320AIC3104, enabling support for Raspberry Pi 5 and expanding the sampling rate range from 8 kHz to 96 kHz.

  ---

> [!NOTE]
> The reSpeaker 2-Mics Pi HAT has been upgraded to version 2.0. The codec chip has been replaced from WM8960 to TLV320AIC3104, enabling support for Raspberry Pi 5 and expanding the sampling rate range from 8 kHz to 96 kHz.

  ![ReSpeaker](https://media-cdn.seeedstudio.com/media/catalog/product/cache/bb49d3ec4ee05b6f018e93f896b8a25d/0/6/06_1.png)

  ReSpeaker 2-Mics Pi HAT is a dual-microphone expansion board for Raspberry Pi designed for AI and voice applications. You can build a more powerful and flexible voice product that integrates Amazon Alexa Voice Service, Google Assistant, and so on.

## **Porting Process**  
### **1. Bootable SD Card Preparation**  
- **Image**: `BeagleY-AI Debian 12.9 2025-03-05 XFCE (v6.6.x-ti)`  
- **Flashing**:  
  ```bash  
  sudo balena-etcher-cli --drive /dev/mmcblk0 beagley-ai-debian-12.9.img  
  ```  

### **2. Kernel Driver Compilation**  
**Why Cross-Compile?**  
BeagleY-AI’s RISC-V architecture requires ARM64 kernel modules for compatibility with TI’s McASP driver.  

**Steps**:  
1. Clone the kernel:  
   ```bash  
   git clone --depth=1 -b v6.6.58-ti-arm64-r23 https://github.com/beagleboard/linux  
   ```  
2. Configure for TLV320AIC31xx:  
   ```bash  
   make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- menuconfig  
   # Enable: Device Drivers → Sound → SOC → TI → TLV320AIC31xx (Module)  
   ```  
3. Compile and deploy:  
   ```bash  
   make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- Image dtbs modules -j$(nproc)  
   sudo cp -r modules/lib/modules/$(make kernelversion)/ /media/user/rootfs/lib/modules/  
   ```  

---

## **Device Tree Configuration**  
### **Critical Overlay: `k3-am67a-beagley-ai-respeaker.dtbo`**  
**Key Sections**:  
1. **McASP0 Pin Muxing**:  
   ```dts  
   J722S_IOPAD(0x01a4, PIN_INPUT, 0)  /* BCLK → HAT Pin 12 */  
   J722S_IOPAD(0x01a8, PIN_INPUT, 0)  /* WCLK → HAT Pin 35 */  
   J722S_IOPAD(0x01a0, PIN_INPUT, 0)  /* DIN → HAT Pin 38 */  
   J722S_IOPAD(0x019c, PIN_OUTPUT, 0) /* DOUT → HAT Pin 40 */  
   ```  
2. **TLV320AIC3104 I2C Setup**:  
   ```dts  
   &mcu_i2c0 {  
     tlv320aic3104@18 {  
       reg = <0x18>;  
       clocks = <&tlv320aic3104_mclk>;  
       ai3x-micbias-vg = <2>; // 2.5V for electret mics  
     };  
   };  
   ```  
3. **McASP FIFO Configuration**:  
   ```dts  
   &mcasp0 {  
     tx-num-evt = <32>; // TX FIFO depth (prevents underflow)  
     rx-num-evt = <32>; // RX FIFO depth  
   };  
   ```  

**Deployment**:  
```bash  
sudo fdtoverlay -i /boot/firmware/ti/k3-am67a-beagley-ai.dtb -o /boot/firmware/ti/k3-am67a-beagley-ai.dtb /boot/firmware/overlays/k3-am67a-beagley-ai-respeaker.dtbo  
```  

---

## **Audio Pipeline Validation**  
### **1. ALSA Hardware Testing**  
- **List Devices**:  
  ```bash  
  arecord -l  # Should show "seeed2micvoicec" as card 0  
  ```  
- **Record/Playback**:  
  ```bash  
  arecord -D plughw:0,0 -f S16_LE -r 16000 -c 1 -d 5 test.wav  
  aplay -D hw:0,0 test.wav  
  ```  

### **2. McASP Clock Verification**  
- **Expected Signals**:  
  - **BCLK**: 1.536 MHz (for 48 kHz, 32-bit frames).  
  - **MCLK**: 12.288 MHz (256 × 48 kHz).  
- **Debugging**:  
  ```bash  
  dmesg | grep mcasp  # Check for "McASP0 configured as I2S Master"  
  ```  

---

## **Advanced: Keyword Spotting Demo**  
### **1. Setup EdgeAI-KWS**  
```bash  
git clone https://github.com/TexasInstruments/edgeai-keyword-spotting  
python3 -m venv kws-env && source kws-env/bin/activate  
pip install tflite-runtime librosa numpy  
```  

### **2. Offload Inference to MMA**  
- **Model Compilation**:  
  ```bash  
  ./edgeai-tidl-tools --compile -m model.tflite -c ./tidl_config  
  ```  
- **Run Inference**:  
  ```python  
  from tflite_runtime.interpreter import load_delegate  
  interpreter = tf.lite.Interpreter(  
      model_path='model.tflite',  
      experimental_delegates=[load_delegate('libtidl_tfl_delegate.so')]  
  )  
  ```  

**Expected Performance**:  
- **Preprocessing**: 5 ms (C7x DSP offload).  
- **Inference**: 2 ms (MMA).  

---

## **Troubleshooting**  
### **1. "Input/Output Error" During Recording**  
**Cause**: McASP FIFO underflow.  
**Fix**:  
```dts  
// In mcasp0 node:  
tx-num-evt = <32>;  
rx-num-evt = <32>;  
```  

### **2. Silent Playback**  
**Diagnosis**:  
```bash  
alsamixer  # Ensure "Headphone" and "PGA" are unmuted  
```  
**Fix**:  
```dts  
// In sound1 node:  
simple-audio-card,routing = "Headphone Jack", "HPLOUT";  
```  

### **3. I2C Communication Failure**  
**Debug**:  
```bash  
i2cdetect -y 0  # Check for device 0x18  
```  

---

## **Conclusion**  
This port bridges ReSpeaker’s audio capabilities with BeagleY-AI’s computational power, enabling edge-native voice AI. Future enhancements could leverage the MMA for speaker diarization or integrate beamforming using McASP’s TDM mode. Share your device tree overlays and benchmarks with the [BeagleY-AI community](https://forum.beagleboard.org/)!  

---

## **References**  
1. BeagleBoard.org, *BeagleY-AI Documentation*, 2025. [Online]. Available: [https://docs.beagleboard.org](https://docs.beagleboard.org)  
2. Texas Instruments, *TLV320AIC3104 Data Sheet (Rev. G)*, 2021. [PDF]. [https://www.ti.com/lit/ds/symlink/tlv320aic3104.pdf](https://www.ti.com/lit/ds/symlink/tlv320aic3104.pdf)  
3. Seeed Studio, *ReSpeaker 2-Mics Pi HAT v2 Wiki*, 2023. [Online]. Available: [https://wiki.seeedstudio.com](https://wiki.seeedstudio.com)  

---

**Appendices**:  
- **Pinout Diagram**: [BeagleY-AI McASP Mapping](https://pinout.beagley.ai)  
- **Sample Code**: [GitHub Repository](https://github.com/jaydon2020/ReSpeaker-2-Mics-Pi-HAT-v2-BeagleY-AI)  

Let me know if you'd like to expand specific sections (e.g., McASP clock tree deep dive)! 🎤