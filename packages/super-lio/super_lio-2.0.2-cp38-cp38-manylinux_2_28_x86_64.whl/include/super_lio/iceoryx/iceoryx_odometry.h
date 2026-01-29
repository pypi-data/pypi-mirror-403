#ifndef ICEORYX_ODOMETRY_H
#define ICEORYX_ODOMETRY_H

#include "iceoryx_pointcloud2.h"

struct OdometryQuaternion {
    static constexpr const char* IOX2_TYPE_NAME = "Quaternion";
    
    double x;
    double y;
    double z;
    double w;
};

struct OdometryVector3 {
    static constexpr const char* IOX2_TYPE_NAME = "Vector3";
    
    double x;
    double y;
    double z;
};

struct OdometryPoint {
    static constexpr const char* IOX2_TYPE_NAME = "Point";
    
    double x;
    double y;
    double z;
};

struct OdometryPose {
    static constexpr const char* IOX2_TYPE_NAME = "Pose";
    
    OdometryPoint position;
    OdometryQuaternion orientation;
};

using PoseCovarianceArray = double[36];

struct OdometryPoseWithCovariance {
    static constexpr const char* IOX2_TYPE_NAME = "PoseWithCovariance";
    
    OdometryPose pose;
    PoseCovarianceArray covariance;
};

struct OdometryTwist {
    static constexpr const char* IOX2_TYPE_NAME = "Twist";
    
    OdometryVector3 linear;
    OdometryVector3 angular;
};

using TwistCovarianceArray = double[36];

struct OdometryTwistWithCovariance {
    static constexpr const char* IOX2_TYPE_NAME = "TwistWithCovariance";
    
    OdometryTwist twist;
    TwistCovarianceArray covariance;
};

struct Odometry {
    static constexpr const char* IOX2_TYPE_NAME = "Odometry";
    
    Header header;
    OdometryPoseWithCovariance pose;
    OdometryTwistWithCovariance twist;
};

#endif // ICEORYX_ODOMETRY_H
