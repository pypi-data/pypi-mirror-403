#ifndef ICEORYX_CONVERTER_H
#define ICEORYX_CONVERTER_H

#include "iceoryx_pointcloud2.h"
#include <pcl/point_cloud.h>
#include <pcl/point_types.h>
#include <string>
#include <memory>

#include "basic/alias.h"

namespace IceoryxConverter {

/**
 * @brief Convert Iceoryx PointCloud2 to PCL PointCloud
 * @param msg Iceoryx PointCloud2 message
 * @param pcl_out Output PCL point cloud
 */
void convertToPCL(const PointCloud2& msg, BASIC::CloudPtr& pcl_out);

/**
 * @brief Get timestamp from PointCloud2 message
 * @param msg Iceoryx PointCloud2 message
 * @return Timestamp in seconds
 */
double getTimestamp(const PointCloud2& msg);

/**
 * @brief Extract a single point from PointCloud2 message
 * @param msg Iceoryx PointCloud2 message
 * @param index Point index
 * @param x Output x coordinate
 * @param y Output y coordinate
 * @param z Output z coordinate
 * @param intensity Output intensity
 * @param offset_time Output offset time
 * @return true if extraction successful
 */
bool extractPoint(const PointCloud2& msg, size_t index,
                  float& x, float& y, float& z, 
                  float& intensity, float& offset_time);

/**
 * @brief Convert PCL PointCloud to Iceoryx PointCloud2
 * @param pcl_in Input PCL point cloud
 * @param msg_out Output Iceoryx PointCloud2 message
 * @return true if conversion successful
 */
bool convertToIceoryx2(const BASIC::CloudPtr& pcl_in, PointCloud2& msg_out);

} // namespace IceoryxConverter

#endif // ICEORYX_CONVERTER_H
