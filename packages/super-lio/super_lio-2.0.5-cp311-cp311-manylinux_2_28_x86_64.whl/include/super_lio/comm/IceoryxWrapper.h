/**
 * @file IceoryxWrapper.h
 * @brief Iceoryx2-based communication wrapper replacing ROSWrapper
 */

#ifndef ICEORYX_WRAPPER_H_
#define ICEORYX_WRAPPER_H_

#include <map>
#include <tuple>
#include <deque>
#include <vector>
#include <atomic>
#include <thread>
#include <mutex>
#include <condition_variable>
#include <memory>

#include <pcl/point_types.h>
#include <pcl/point_cloud.h>

#include "iceoryx/iceoryx_pointcloud2.h"
#include "iceoryx/iceoryx_imu.h"
#include "iceoryx/iceoryx_odometry.h"
#include "iceoryx/iceoryx_converter.h"

#include "lio/params.h"
#include "basic/alias.h"
#include "basic/logs.h"
#include "basic/Manifold.h"
#include "common/ds.h"

#include "lio/ESKF.h"

// iceoryx2 types are included in the .cpp file to avoid header conflicts
// The wrapper class uses pimpl idiom internally

namespace LI2Sup {

/**
 * @brief Load parameters from YAML file
 * @param config_path Path to the YAML configuration file
 */
void LoadParamFromYAML(const std::string& config_path);

/**
 * @brief Convert Livox CustomMsg format to internal point cloud
 * @param msg Iceoryx PointCloud2 message (Livox format)
 * @param point_cloud Output point cloud with offset time
 * @param start_time Output start timestamp
 * @param end_time Output end timestamp
 */
void livox2Internal(const PointCloud2& msg, 
                    pcl::PointCloud<PointXTZIT>::Ptr& point_cloud,
                    double& start_time, double& end_time);

/**
 * @brief IceoryxWrapper - Communication layer using Iceoryx2
 * Replaces ROSWrapper for ROS-free communication
 */
class IceoryxWrapper {
public:
    IceoryxWrapper();
    ~IceoryxWrapper();
    
    using Ptr = std::shared_ptr<IceoryxWrapper>;
    
    /**
     * @brief Initialize Iceoryx2 communication
     * @return true if initialization successful
     */
    bool init();
    
    /**
     * @brief Start subscriber threads
     */
    void start();
    
    /**
     * @brief Stop subscriber threads
     */
    void stop();
    
    /**
     * @brief Synchronize measurements (lidar + IMU)
     * @param meas Output synchronized measurements
     * @return true if synchronization successful
     */
    bool sync_measure(MeasureGroup& meas);
    
    /**
     * @brief Set ESKF pointer for IMU prediction
     */
    void setESKF(ESKF::Ptr& eskf) { eskf_ = eskf; }
    
    /**
     * @brief Clear data buffers
     */
    void clear() {
        std::lock_guard<std::mutex> lock(buffer_mutex_);
        lidar_buffer_.clear();
        imu_buffer_.clear();
        lidar_pushed_ = false;
        last_timestamp_imu_ = -1.0;
        last_timestamp_lidar_ = -1.0;
    }
    
    /**
     * @brief Publish odometry
     * @param state Navigation state to publish
     */
    void pub_odom(const NavState& state);
    
    /**
     * @brief Publish world frame point cloud
     * @param pc Point cloud to publish
     * @param time Timestamp
     */
    void pub_cloud_world(const BASIC::CloudPtr& pc, double time);
    
    /**
     * @brief Spin once - process pending callbacks
     */
    void spin_once();
    
    /**
     * @brief Check if running
     */
    bool isRunning() const { return running_.load(); }
    
    /**
     * @brief Set global map for visualization (stub for relocation)
     */
    void set_global_map(const BASIC::CloudPtr& global_map) {
        // In Iceoryx version, we could publish this or just store for later
        global_map_ = global_map;
    }
    
    /**
     * @brief Set initial data for relocation (stub)
     * @param init_pose Initial pose reference
     * @param flg_get_init_guess Flag for init guess
     * @param flg_finish_init Flag for finish init
     */
    void set_initial_data(BASIC::SE3& init_pose, bool& flg_get_init_guess, bool flg_finish_init = false) {
        // In standalone mode, initial pose is loaded from config
        // This is a compatibility stub
        (void)init_pose;
        (void)flg_get_init_guess;
        (void)flg_finish_init;
    }

private:
    // Subscriber thread functions
    void imuSubscriberThread();
    void lidarSubscriberThread();
    
    // Data processing
    void processImu(const Imu& msg);
    void processLidar(const PointCloud2& msg);
    
private:
    std::atomic<bool> running_{false};
    std::thread imu_thread_;
    std::thread lidar_thread_;
    
    // Data buffers
    std::mutex buffer_mutex_;
    std::deque<IMUData> imu_buffer_;
    std::deque<LidarData> lidar_buffer_;
    bool lidar_pushed_ = false;
    double last_timestamp_imu_ = -1.0;
    double last_timestamp_lidar_ = -1.0;
    
    // ESKF for IMU prediction
    ESKF::Ptr eskf_{nullptr};
    
    // Publisher state
    std::mutex pub_mutex_;
    
    // Iceoryx service names (loaded from config)
    std::string imu_service_name_;
    std::string lidar_service_name_;
    std::string odom_service_name_;
    std::string cloud_service_name_;
    
    // Global map for relocation
    BASIC::CloudPtr global_map_;
};

// Global parameters for Iceoryx services
extern std::string g_iceoryx_imu_service;
extern std::string g_iceoryx_lidar_service;
extern std::string g_iceoryx_odom_service;
extern std::string g_iceoryx_cloud_service;

} // namespace LI2Sup

#endif // ICEORYX_WRAPPER_H_
