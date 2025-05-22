<?php
// Set error reporting for debugging
error_reporting(E_ALL);
ini_set('display_errors', 1);

// Response array
$response = array();

// Check if file was uploaded
if (isset($_FILES['snake_image']) && $_FILES['snake_image']['error'] === UPLOAD_ERR_OK) {
    // Get file details
    $file_tmp = $_FILES['snake_image']['tmp_name'];
    $file_name = $_FILES['snake_image']['name'];
    $file_ext = strtolower(pathinfo($file_name, PATHINFO_EXTENSION));
    
    // Check file extension
    $allowed_extensions = array('jpg', 'jpeg', 'png');
    if (!in_array($file_ext, $allowed_extensions)) {
        $response['status'] = 'error';
        $response['message'] = 'Only JPG, JPEG, and PNG files are allowed.';
        echo json_encode($response);
        exit;
    }
    
    // Generate unique filename
    $new_file_name = uniqid() . '.' . $file_ext;
    $upload_path = 'uploads/' . $new_file_name;
    
    // Move uploaded file to destination
    if (move_uploaded_file($file_tmp, $upload_path)) {
        // Get absolute path for Python script
        $absolute_path = realpath($upload_path);
        
        // Call Python script for prediction
        $command = 'cd /home/saiful/Rintu/projects/snake-detection && source /home/saiful/anaconda3/envs/snake/bin/activate && python predict_snake.py "' . $absolute_path . '" 2>&1';
        $output = shell_exec($command);
        
        // Parse JSON output from Python script
        $prediction_result = json_decode($output, true);
        
        // Check if prediction was successful
        if (isset($prediction_result['success']) && $prediction_result['success']) {
            $response['status'] = 'success';
            $response['prediction'] = $prediction_result;
            $response['uploaded_image'] = $upload_path;
        } else {
            $response['status'] = 'error';
            $response['message'] = isset($prediction_result['error']) ? $prediction_result['error'] : 'Unknown error during prediction';
            $response['debug'] = $output;
        }
    } else {
        $response['status'] = 'error';
        $response['message'] = 'Failed to save uploaded file.';
    }
} else {
    $response['status'] = 'error';
    $response['message'] = 'No file uploaded or upload error occurred.';
    if (isset($_FILES['snake_image'])) {
        $response['error_code'] = $_FILES['snake_image']['error'];
    }
}

// Return JSON response
header('Content-Type: application/json');
echo json_encode($response);
?>
