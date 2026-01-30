#include <iostream>

#include <phoxi_sensor.h>


PhoXiSensor::PhoXiSensor(const std::string& device_name): device_name(device_name) { }

PhoXiSensor::~PhoXiSensor() {
    stop();
}

bool PhoXiSensor::start() {
    return connect() && device->StartAcquisition();
}

bool PhoXiSensor::connect() {
    pho::api::PhoXiFactory factory;

    // Check if the PhoXi Control Software is running
    if (!factory.isPhoXiControlRunning()) {
        std::cout << "PhoXi Control Software is not running" << std::endl;
        return false;
    }

    if (device_name.empty()) {
        std::cout << "Device name is empty" << std::endl;
        return false;
    }

    device = factory.CreateAndConnect(device_name, 4000);

    // Check if device was created
    if (!device || !device->isConnected()) {
        std::cout << "Failed to connect to PhoXi device." << std::endl;
        return false;
    }

    device->CapturingSettings->AmbientLightSuppression = true;
    device->TriggerMode = pho::api::PhoXiTriggerMode::Software;

    return true;
}

void PhoXiSensor::stop() {
    if (!device) {
        return;
    }

    if (device->isAcquiring()) {
        device->StopAcquisition();
    }

    device->Disconnect(true, false);
}

bool PhoXiSensor::frames() {
    if (!device || !device->isConnected()) {
        return false;
    }

    device->ClearBuffer();
    if (!device->isAcquiring()) {
        std::cout << "Your device is not started for acquisition!" << std::endl;
        return false;
    }

    last_frame_id = device->TriggerFrame();
    if (last_frame_id < 0) {
        std::cout << "Trigger was unsuccessful!" << std::endl;
        return false;
    }

    frame = device->GetSpecificFrame(last_frame_id, 5000);
    if (!frame) {
        std::cout << "Failed to retrieve the frame!" << std::endl;
        return false;
    }

    const auto& camera_matrix = frame->Info.CameraMatrix;
    intrinsics.fx = camera_matrix[0][0];
    intrinsics.fy = camera_matrix[1][1];
    intrinsics.cx = camera_matrix[0][2];
    intrinsics.cy = camera_matrix[1][2];
    intrinsics.distortion_coefficients = frame->Info.DistortionCoefficients;
    return true;
}

std::shared_future<bool> PhoXiSensor::frames_async() {
    return std::async(std::launch::async, &PhoXiSensor::frames, this);
}

bool PhoXiSensor::save_last_frame(const std::filesystem::path& path) {
    if (last_frame_id == -1) {
        return false;
    }
    return device->SaveLastOutput(path.string(), last_frame_id);
}

std::vector<std::vector<float>> PhoXiSensor::get_depth_map() const {
    const int width = frame->DepthMap.Size.Width;
    const int height = frame->DepthMap.Size.Height;

    std::vector<std::vector<float>> depth_map;
    depth_map.resize(height);
    for (size_t i = 0; i < height; i++) {
        depth_map[i].resize(width);

        for (size_t j = 0; j < width; j++) {
            depth_map[i][j] = frame->DepthMap.At(i, j) / 1000.0;  // from [mm] to [m]
        }
    }
    return depth_map;
}

std::vector<std::vector<float>> PhoXiSensor::get_texture() const {
    const int width = frame->Texture.Size.Width;
    const int height = frame->Texture.Size.Height;

    std::vector<std::vector<float>> texture;
    texture.resize(height);
    for (size_t i = 0; i < height; i++) {
        texture[i].resize(width);

        for (size_t j = 0; j < width; j++) {
            texture[i][j] = frame->Texture.At(i, j);
        }
    }
    return texture;
}
