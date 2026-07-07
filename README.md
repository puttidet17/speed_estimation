# 🚗 Vehicle Speed Estimation with YOLOv8 & ROS 2

ระบบตรวจจับความเร็วรถยนต์อัจฉริยะโดยใช้คอมพิวเตอร์วิทัศน์ (Computer Vision) ร่วมกับระบบปฏิบัติการหุ่นยนต์ (ROS 2) เพื่อประมวลผลวิดีโอจากกล้องจราจร แยกรถยนต์ คำนวณความเร็ว (km/h) ตรวจสอบการเลี้ยวตัดเลน (Invalid Merger) และทำการบันทึกข้อมูลจราจรในรูปแบบ Decentralized Architecture

## ✨ Features (ความสามารถของระบบ)
- **AI Tracking:** ใช้ YOLOv8 ร่วมกับ ByteTrack ในการตรวจจับและติดตามรถยนต์ (Classes: Car, Motorcycle, Bus, Truck)
- **Speed Estimation:** คำนวณความเร็วรถยนต์แบบ Real-time โดยใช้ระบบ ROI Gating (Start/End Gate)
- **Turn & Merge Detection:** มี Noise Filter และระบบตรวจสอบทิศทางรถยนต์เพื่อคัดกรองรถที่เลี้ยวตัดเลนออกจากการคำนวณความเร็ว
- **ROS 2 Architecture:** แยกการทำงานเป็น 2 Node อิสระตามมาตรฐานวิทยาการหุ่นยนต์:
  - `speed_detector` (Publisher): ประมวลผล AI และโยนข้อมูลสตรีมมิ่งออกอากาศเป็น JSON
  - `speed_subscriber` (Subscriber): ดักรับข้อมูล JSON เพื่อแปลงและบันทึกลงไฟล์ตารางอัตโนมัติ
- **Data Logging:** บันทึกประวัติ วันเวลา ไอดีรถ ความเร็ว และสถานะลงไฟล์ `speed_logs.csv` เพื่อนำไปวิเคราะห์ต่อได้ทันที

## 🛠️ System Architecture (โครงสร้างของระบบ)
[Node: speed_detector] --(Topic: /vehicle/speed_data [JSON])--> [Node: speed_subscriber] --> [File: speed_logs.csv]

## 🚀 How to Run (วิธีการติดตั้งและใช้งาน)
1. Clone รีโพสิทอรีนี้ลงเครื่อง
2. เปิดใช้งาน Environment และ Build แพ็กเกจ ROS 2:
   ```bash
   cd ~/ros2_ws
   colcon build --packages-select ai_tracker --symlink-install
   source install/setup.bash
3. รัน Node ฝั่งบันทึกข้อมูล (Terminal 1):
   ```bash
   ros2 run ai_tracker speed_subscriber
4. รัน Node ฝั่ง AI ประมวลผลหลัก (Terminal 2):
   ```bash
   ros2 run ai_tracker speed_detector
