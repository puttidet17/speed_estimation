import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import json
import csv
import os
from datetime import datetime

class SpeedSubscriber(Node):
    def __init__(self):
        super().__init__('speed_subscriber_node')
        self.subscription = self.create_subscription(String, '/vehicle/speed_data', self.listener_callback, 10)
        self.csv_path = "data/speed_logs.csv"

        os.makedirs("data", exist_ok=True)
        if not os.path.exists(self.csv_path):
            with open(self.csv_path, mode='w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Timestamp", "Vehicle_ID", "Speed(km/h)", "Status"])

        self.get_logger().info("ROS 2 Speed Subscriber Node (CSV Logger) has been started!")

    def listener_callback(self, msg):
        try:
            data = json.loads(msg.data)
            for vehicle in data.get("vehicles", []):
                speed = vehicle.get("speed(km/h)")
                v_id = vehicle.get("id")
                status = vehicle.get("status")

                if speed is not None:
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    with open(self.csv_path, mode='a', newline='') as f:
                        writer = csv.writer(f)
                        writer.writerow([timestamp, v_id, speed, status])
                        self.get_logger().info(f"Saved to CSV -> ID:{v_id} | Speed:{speed} km/h | Status:{status}")
            
        except Exception as e:
            self.get_logger().error(f"Error writing to CSV: {e}")

def main(args=None):
    rclpy.init(args=args)
    node = SpeedSubscriber()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__mian__':
    main()