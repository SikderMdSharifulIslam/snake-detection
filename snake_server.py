#!/usr/bin/env python3
import os
import sys
import json
import time
import base64
import http.server
import socketserver
import urllib.parse
from io import BytesIO
from ultralytics import YOLO

# Dictionary mapping class indices to snake information
SNAKE_INFO = {
    0: {
        "name": "Green Vine Snake",
        "scientific_name": "Ahaetulla nasuta",
        "venomous": "Mildly venomous",
        "description": "A slender, bright green tree snake with a pointed snout. Found in forests across South and Southeast Asia."
    },
    1: {
        "name": "King Cobra",
        "scientific_name": "Ophiophagus hannah",
        "venomous": "Highly venomous",
        "description": "The world's longest venomous snake. Found predominantly in forests from India through Southeast Asia."
    },
    2: {
        "name": "Rock Python",
        "scientific_name": "Python sebae",
        "venomous": "Non-venomous",
        "description": "One of the largest snake species in Africa, known for its size and strength. Constrictor that preys on mammals and birds."
    },
    3: {
        "name": "Russell's Viper",
        "scientific_name": "Daboia russelii",
        "venomous": "Highly venomous",
        "description": "One of the most dangerous snakes in Asia, responsible for many snakebite incidents. Known for its distinctive chain-like pattern."
    },
    4: {
        "name": "Saw Scaled Viper",
        "scientific_name": "Echis carinatus",
        "venomous": "Highly venomous",
        "description": "Small but highly venomous snake known for its distinctive threat display of rubbing its scales together to produce a sawing sound."
    },
    5: {
        "name": "Trinket Snake",
        "scientific_name": "Coelognathus helena",
        "venomous": "Non-venomous",
        "description": "A non-venomous colubrid snake found in South Asia. Known for its attractive pattern and docile nature."
    },
    6: {
        "name": "Checkered Keelback",
        "scientific_name": "Fowlea piscator",
        "venomous": "Non-venomous",
        "description": "A common water snake found across South and Southeast Asia. Feeds primarily on fish and amphibians."
    },
    7: {
        "name": "Cobra",
        "scientific_name": "Naja naja",
        "venomous": "Highly venomous",
        "description": "The Indian cobra is a venomous snake known for its hood display when threatened. One of the 'Big Four' snakes in India."
    },
    8: {
        "name": "Common Krait",
        "scientific_name": "Bungarus caeruleus",
        "venomous": "Highly venomous",
        "description": "One of the most venomous snakes in India. Nocturnal and known for its distinctive black and white bands."
    },
    9: {
        "name": "Rat Snake",
        "scientific_name": "Ptyas mucosa",
        "venomous": "Non-venomous",
        "description": "A large, fast-moving non-venomous snake that feeds primarily on rodents. Common across South and Southeast Asia."
    },
    10: {
        "name": "Wolf Snake",
        "scientific_name": "Lycodon aulicus",
        "venomous": "Non-venomous",
        "description": "A small, nocturnal snake that resembles the venomous krait but is harmless. Named for its wolf-like teeth."
    }
}

# Create directories for uploads and predictions
os.makedirs('frontend/snakeGuardPlus/uploads', exist_ok=True)
os.makedirs('frontend/snakeGuardPlus/predictions', exist_ok=True)

# Load the YOLO model
model_path = "runs/detect/train2/weights/best.pt"
try:
    model = YOLO(model_path)
    print(f"Model loaded successfully from {model_path}")
except Exception as e:
    print(f"Error loading model: {e}")
    model = None

def predict_snake(image_path):
    """
    Predict snake species from an image using a pre-trained YOLO model.

    Args:
        image_path: Path to the image file

    Returns:
        Dictionary with prediction results
    """
    try:
        # Check if image exists
        if not os.path.exists(image_path):
            return {"error": f"Image not found at {image_path}"}

        # Check if model is loaded
        if model is None:
            return {"error": "Model not loaded"}

        # Generate a unique output directory based on timestamp
        timestamp = int(time.time())
        output_dir = f"frontend/snakeGuardPlus/predictions/{timestamp}"
        os.makedirs(output_dir, exist_ok=True)

        # Run prediction
        results = model.predict(image_path, save=True, project=output_dir, name="result", conf=0.25)

        # Process results
        if not results or len(results) == 0:
            return {"error": "No predictions made"}

        # Get the first result (assuming single image input)
        result = results[0]

        # Get the predicted classes and confidence scores
        boxes = result.boxes
        if len(boxes) == 0:
            return {"error": "No snakes detected in the image"}

        # Get the box with highest confidence
        confidences = boxes.conf.tolist()
        max_conf_idx = confidences.index(max(confidences))

        # Get class ID and confidence
        class_id = int(boxes.cls[max_conf_idx].item())
        confidence = confidences[max_conf_idx] * 100  # Convert to percentage

        # Get snake information
        snake_info = SNAKE_INFO.get(class_id, {
            "name": "Unknown Snake",
            "scientific_name": "Unknown",
            "venomous": "Unknown",
            "description": "Information not available for this species."
        })

        # Get the path to the saved prediction image
        prediction_image = os.path.join(output_dir, "result", os.path.basename(image_path))

        # Make sure the prediction image exists
        if not os.path.exists(prediction_image):
            return {"error": f"Prediction image not found at {prediction_image}"}

        # Convert the prediction image path to a relative URL
        prediction_url = "/" + prediction_image

        # Return results
        return {
            "success": True,
            "class_id": class_id,
            "confidence": confidence,
            "snake_info": snake_info,
            "prediction_image": prediction_url
        }

    except Exception as e:
        return {"error": f"Prediction failed: {str(e)}"}

class SnakeDetectionHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # Map URLs to local file paths
        if self.path == '/':
            self.path = '/frontend/snakeGuardPlus/index.html'
        elif self.path == '/identifySnake.html':
            self.path = '/frontend/snakeGuardPlus/identifySnake.html'
        elif self.path.startswith('/frontend/'):
            # Already has the correct path prefix
            pass
        elif self.path.endswith('.png') or self.path.endswith('.jpg') or self.path.endswith('.jpeg'):
            # Handle image files
            self.path = '/frontend/snakeGuardPlus' + self.path

        # Print the requested path for debugging
        print(f"Requested path: {self.path}")

        return http.server.SimpleHTTPRequestHandler.do_GET(self)

    def do_POST(self):
        if self.path == '/predict':
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)

                # Parse the form data
                boundary = self.headers['Content-Type'].split('=')[1].encode()
                form_data = self.parse_multipart(post_data, boundary)

                if 'image' in form_data:
                    # Save the uploaded image
                    image_data = form_data['image']
                    timestamp = int(time.time())
                    image_filename = f"upload_{timestamp}.jpg"
                    image_path = os.path.join('frontend/snakeGuardPlus/uploads', image_filename)

                    with open(image_path, 'wb') as f:
                        f.write(image_data)

                    print(f"Image saved to {image_path}")

                    # Predict the snake
                    result = predict_snake(image_path)

                    # Format the response for the frontend
                    response = {
                        "status": "success",
                        "prediction": result
                    }

                    # Print the response for debugging
                    print(f"Response: {json.dumps(response, indent=2)}")

                    # Send the response
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps(response).encode())
                else:
                    self.send_response(400)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        "status": "error",
                        "message": "No image found in request"
                    }).encode())
            except Exception as e:
                print(f"Error processing request: {str(e)}")
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "status": "error",
                    "message": f"Server error: {str(e)}"
                }).encode())
        else:
            self.send_response(404)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "error",
                "message": "Endpoint not found"
            }).encode())

    def parse_multipart(self, data, boundary):
        form_data = {}
        parts = data.split(b'--' + boundary)

        for part in parts:
            if b'Content-Disposition: form-data;' in part:
                # Extract field name
                header_end = part.find(b'\r\n\r\n')
                if header_end == -1:
                    continue

                header = part[:header_end].decode('utf-8', 'ignore')
                name_start = header.find('name="') + 6
                name_end = header.find('"', name_start)
                field_name = header[name_start:name_end]

                # Extract field value
                field_value = part[header_end + 4:].strip(b'\r\n--')

                form_data[field_name] = field_value

        return form_data

def run_server(port=8000):
    handler = SnakeDetectionHandler

    # Try different ports if the specified one is in use
    max_attempts = 10
    current_port = port

    for attempt in range(max_attempts):
        try:
            # Allow the socket to be reused immediately after the server is stopped
            socketserver.TCPServer.allow_reuse_address = True

            with socketserver.TCPServer(("", current_port), handler) as httpd:
                print(f"Server running at http://localhost:{current_port}")

                # Update the frontend to use this port
                update_frontend_port(current_port)

                httpd.serve_forever()
                break
        except OSError as e:
            if e.errno == 98:  # Address already in use
                print(f"Port {current_port} is already in use, trying port {current_port + 1}")
                current_port += 1
                if attempt == max_attempts - 1:
                    print(f"Could not find an available port after {max_attempts} attempts")
                    raise
            else:
                raise

def update_frontend_port(port):
    """Update the frontend HTML file to use the correct port"""
    try:
        html_path = "frontend/snakeGuardPlus/identifySnake.html"
        with open(html_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        # Replace the port in the fetch URL
        import re
        new_content = re.sub(
            r'fetch\([\'"]http://localhost:\d+/predict[\'"]',
            f'fetch("http://localhost:{port}/predict"',
            content
        )

        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(new_content)

        print(f"Updated frontend to use port {port}")
    except Exception as e:
        print(f"Warning: Could not update frontend port: {e}")

if __name__ == "__main__":
    port = 8000
    if len(sys.argv) > 1:
        port = int(sys.argv[1])

    run_server(port)
