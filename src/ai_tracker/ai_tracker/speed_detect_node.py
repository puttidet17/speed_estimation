import cv2
from ultralytics import YOLO
import json

# --- เพิ่มไลบรารีของ ROS 2 เข้ามา ---
import rclpy
from rclpy.node import Node
from std_msgs.msg import String  # ใช้ String ในการส่งข้อมูล JSON ออกอากาศ

# --- สร้างคลาสสำหรับครอบสคริปต์ของคุณ ---
class VehicleSpeedPublisher(Node):
    def __init__(self):
        super().__init__('speed_detector_node')
        
        # สร้างหัวข้อกระจายสัญญาณ (Publisher) ชื่อ /vehicle/speed_data
        self.publisher_ = self.create_publisher(String, '/vehicle/speed_data', 10)
        self.get_logger().info("ROS 2 Speed Detector Node has been started!")
        
        # สั่งให้ลูป AI ตัวหลักทำงาน
        self.run_detector()

    def run_detector(self):
        # ==========================================================
        # 🚨 โค้ดต้นฉบับของคุณ Puttidet แบบเป๊ะๆ 100%
        # ==========================================================
        # Load model -------------------------------
        model = YOLO("yolov8s.pt")

        #Input Video
        video_path = "data/cars.mp4"
        cap = cv2.VideoCapture(video_path)

        if not cap.isOpened():
            self.get_logger().error(f"Error: Could not open video file at {video_path}")
            return

        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = int(cap.get(cv2.CAP_PROP_FPS))

        # Output Video --------------------------------
        output_path = "data/output_speed_estimation.mp4"
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (frame_width, frame_height))

        # Configurartion -------------------------------
        LINE_START_Y = int(frame_height * 0.40)
        LINE_END_Y = int(frame_height * 0.60)
        ROAD_DISTANCE_METERS = 45.0
        ROAD_MIDDLE_X = int(frame_width * 0.28)
        VALIDATION_BUFFER_Y = LINE_START_Y + 100

        track_history = {}
        track_start_frames = {}
        speed_cache = {}
        start_positions_x = {}
        turn_status = {}

        frame_count = 0

        # track (เพิ่ม rclpy.ok() เพื่อให้รองรับการทำงานของ ROS 2)
        while cap.isOpened() and rclpy.ok():
            success, frame = cap.read()
            if not success:
                break
            
            frame_count += 1

            frame_data = {
                "frame_count": frame_count,
                "vehicles": []
            }

            results = model.track(
                frame,
                device=0,
                classes=[2,3,5,7],
                persist=True,
                tracker="bytetrack.yaml",
                conf=0.35,
                iou=0.5,
                verbose=False
            )

            # Gate Line ----------------------------------
            cv2.line(frame, (0, LINE_START_Y), (frame_width, LINE_START_Y), (0, 255, 0), 2)
            cv2.line(frame, (0, LINE_END_Y), (frame_width, LINE_END_Y), (0, 0, 255), 2)
            cv2.putText(frame, "START GATE", (10, LINE_START_Y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            cv2.putText(frame, "END GATE", (10, LINE_END_Y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            cv2.line(frame, (ROAD_MIDDLE_X, 0), (ROAD_MIDDLE_X, frame_height), (255, 255, 0), 2)

            if results[0].boxes.id is not None:
                boxes = results[0].boxes.xyxy.cpu().numpy()
                track_ids = results[0].boxes.id.cpu().numpy().astype(int)
                clss = results[0].boxes.cls.cpu().numpy().astype(int)

                for box, track_id, cls in zip(boxes, track_ids, clss):
                    x1, y1, x2, y2 = box
                    cx = int((x1 + x2) / 2)
                    cy = int((y1 + y2) / 2)

                    if cx < ROAD_MIDDLE_X:
                        continue
                    box_width = x2 - x1
                    box_height = y2 - y1
                    if box_height > (box_width * 2.0) or (box_width * box_height) > (frame_width * frame_height * 0.20):
                        continue

                    if track_id not in turn_status:
                        turn_status[track_id] = "Straight" 

                    if track_id not in track_history:
                        track_history[track_id] = []
                        start_positions_x[track_id] = cx
                        entry_point_y = cy

                        if entry_point_y > VALIDATION_BUFFER_Y:
                            turn_status[track_id] = "Invalid_Merger"

                    track_history[track_id].append(cy) 

                    is_invalid = (turn_status.get(track_id) == "Invalid_Merger")

                    # ROI Gating (speed)
                    if not is_invalid:
                        if cy >= LINE_START_Y and track_id not in track_start_frames and cy < LINE_END_Y:
                            track_start_frames[track_id] = frame_count

                        if cy >= LINE_END_Y and track_id in track_start_frames and track_id not in speed_cache:
                            start_frame = track_start_frames[track_id]
                            frames_elapsed = frame_count - start_frame
                            elapsed_time_sec = frames_elapsed / fps 

                            if elapsed_time_sec > 0:
                                speed_mps = ROAD_DISTANCE_METERS / elapsed_time_sec
                                speed_cache[track_id] = int(speed_mps * 3.6)

                        if track_id in start_positions_x:
                            dx = cx - start_positions_x[track_id]
                            dy = cy - LINE_START_Y
                            if dy > 30 :
                                move_ratio = dx / dy
                                if move_ratio > 0.60:
                                    turn_status[track_id] = "Turn Left"
                                else:
                                    turn_status[track_id] = "Straight"
                            else:
                                turn_status[track_id] = "Straight"

                    # Noise Filter -----------------------------------
                    if len(track_history[track_id]) > 5 :
                        if is_invalid:
                            speed_text = "N/A (Merge)"
                            status = "Unknown"
                            speed_val = None
                        else:
                            speed_text = f"{speed_cache[track_id]} km/h" if track_id in speed_cache else "Calculating..."
                            status = turn_status.get(track_id, "Straight")
                            speed_val = speed_cache.get(track_id, None)

                        label = f"ID:{track_id} {speed_text} | {status}"

                        vehicle_info = {
                            "id" : int(track_id),
                            "speed(km/h)" : speed_val,
                            "status" : status
                        }
                        frame_data["vehicles"].append(vehicle_info)

                        label_x = int(x1)
                        if label_x + 300 > frame_width:
                            label_x = frame_width - 320
                        
                        label_y = int(y1) - 15
                        if label_y < 40:
                            label_y = int(y2) + 40

                        cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (255, 255, 255), 2)
                        cv2.putText(frame, label, (label_x, label_y), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 0), 3)

            # --- 🌟 ไฮไลต์เด็ด: จุดยิงข้อมูลออกอากาศ 🌟 ---
            json_payload = json.dumps(frame_data)
            
            ros_msg = String()
            ros_msg.data = json_payload
            self.publisher_.publish(ros_msg) # ยิงข้อมูลออกไปที่ Topic
            
            out.write(frame)

        cap.release()
        out.release()
        self.get_logger().info("Process Completed!")

# --- ฟังก์ชันเริ่มต้นการทำงานของ ROS 2 ---
def main(args=None):
    rclpy.init(args=args)
    node = VehicleSpeedPublisher()
    rclpy.spin_once(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()