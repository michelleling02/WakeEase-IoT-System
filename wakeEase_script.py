import pymongo
import paho.mqtt.client as mqtt
from datetime import datetime
import pytz  # To handle timezone conversions

# MongoDB configuration
mongo_client = pymongo.MongoClient("mongodb://localhost:27017/")
db = mongo_client["WakeEase"]

# MQTT configuration
mqtt_broker_address = "yourexternalIP" # Replace with your VM instance external IP address
mqtt_topics = [("notification", 0), ("led_duration", 0), ("fan_duration", 0), ("sleep_duration", 0), ("response_time", 0)]  # List of topics to subscribe to

# Define your local timezone
local_timezone = pytz.timezone("Asia/Kuala_Lumpur")  # Replace with your local timezone

# Define the callback function for connection
def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print(f"\n[INFO] Successfully connected to MQTT broker")
        print(f"[INFO] Subscribed to topics: {[t[0] for t in mqtt_topics]}\n")
        client.subscribe(mqtt_topics)  # Subscribe to all topics in the list

# Define the callback function for ingesting data into MongoDB
def on_message(client, userdata, message):
    payload = message.payload.decode("utf-8")
    topic = message.topic

    # Convert current timestamp to local datetime
    timestamp = datetime.now(pytz.utc).astimezone(local_timezone)
    date_str = timestamp.strftime("%Y-%m-%d")
    time_str = timestamp.strftime("%H:%M:%S")

    print(f"=== Received Message ===")
    print(f"  Topic      : {topic}")
    print(f"  Payload    : {payload}")

    # Get or create the collection for the topic
    collection = db[topic]

    # Process data differently based on the topic
    if topic in ["led_duration", "fan_duration", "sleep_duration", "response_time"]:
        try:
            # Extract timing from the payload (e.g., "Button pressed after 8.56 seconds.")
            timing = float(payload.split(" ")[-2])  # Extracts the numeric value before "seconds."
        except (IndexError, ValueError):
            print(f"  [ERROR] Failed to parse timing from payload: {payload}\n")
            return
        
        # Create a simplified document for these topics
        document = {
            "date": date_str,
            "time": time_str,
            "timing": timing
        }
    else:
        # Default document for other topics (e.g., notification)
        document = {
            "timestamp": f"{date_str}T{time_str}Z",
            "data": payload
        }

    # Insert the document into the respective collection
    collection.insert_one(document)
    print(f"  [INFO] Data ingested into MongoDB collection '{topic}'")
    print("========================\n")

# Create a MQTT client instance
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

# Attach the callbacks using explicit methods
client.on_connect = on_connect
client.on_message = on_message

# Connect to the MQTT broker
client.connect(mqtt_broker_address, 1883, 60)

# Start the MQTT loop
client.loop_forever()