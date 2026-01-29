#ifndef ICEORYX_IMU_H
#define ICEORYX_IMU_H

#include "iceoryx_pointcloud2.h"

struct ImuQuaternionNet {
    static constexpr const char* IOX2_TYPE_NAME = "Quaternion";
    
    double x;
    double y;
    double z;
    double w;
};

struct ImuVector3Net {
    static constexpr const char* IOX2_TYPE_NAME = "Vector3";
    
    double x;
    double y;
    double z;
};

using ImuCovarianceArrayNet = double[9];

struct Imu {
    static constexpr const char* IOX2_TYPE_NAME = "Imu";
    
    Header header;
    ImuQuaternionNet orientation;
    ImuCovarianceArrayNet orientation_covariance;
    ImuVector3Net angular_velocity;
    ImuCovarianceArrayNet angular_velocity_covariance;
    ImuVector3Net linear_acceleration;
    ImuCovarianceArrayNet linear_acceleration_covariance;
};

#endif // ICEORYX_IMU_H
