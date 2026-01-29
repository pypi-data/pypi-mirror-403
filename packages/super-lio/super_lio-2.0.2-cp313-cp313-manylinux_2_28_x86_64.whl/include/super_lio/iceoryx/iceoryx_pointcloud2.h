#ifndef ICEORYX_POINTCLOUD2_H
#define ICEORYX_POINTCLOUD2_H

#include <cstdint>
#include <cstring>

#define FRAME_ID_MAX_LEN 64
#define POINT_FIELD_NAME_MAX_LEN 32
#define POINT_FIELD_CAPACITY 6
#define POINTCLOUD_MAX_POINTS 200000
#define POINTCLOUD_POINT_STEP 20
#define POINTCLOUD_MAX_DATA_BYTES (POINTCLOUD_MAX_POINTS * POINTCLOUD_POINT_STEP)


enum class PointFieldDataType : uint8_t {
    INT8 = 1,
    UINT8 = 2,
    INT16 = 3,
    UINT16 = 4,
    INT32 = 5,
    UINT32 = 6,
    FLOAT32 = 7,
    FLOAT64 = 8
};

struct Time {
    static constexpr const char* IOX2_TYPE_NAME = "Time";
    
    uint32_t sec;
    uint32_t nanosec;
    
    double toSec() const {
        return static_cast<double>(sec) + static_cast<double>(nanosec) * 1e-9;
    }
    
    static Time fromSec(double sec) {
        Time t;
        t.sec = static_cast<uint32_t>(sec);
        t.nanosec = static_cast<uint32_t>((sec - static_cast<double>(t.sec)) * 1e9);
        return t;
    }
};

struct Header {
    static constexpr const char* IOX2_TYPE_NAME = "Header";
    
    Time stamp;
    char frame_id[FRAME_ID_MAX_LEN];
    
    void setFrameId(const char* id) {
        size_t len = strlen(id);
        if (len >= FRAME_ID_MAX_LEN) {
            len = FRAME_ID_MAX_LEN - 1;
        }
        strncpy(frame_id, id, len);
        frame_id[len] = '\0';
    }
    
    const char* getFrameId() const {
        return frame_id;
    }
};

struct PointField {
    static constexpr const char* IOX2_TYPE_NAME = "PointField";
    
    char name[POINT_FIELD_NAME_MAX_LEN];
    uint32_t offset;
    PointFieldDataType datatype;
    uint32_t count;
    uint8_t _padding[3];
    
    void setName(const char* n) {
        size_t len = strlen(n);
        if (len >= POINT_FIELD_NAME_MAX_LEN) {
            len = POINT_FIELD_NAME_MAX_LEN - 1;
        }
        strncpy(name, n, len);
        name[len] = '\0';
    }
    
    const char* getName() const {
        return name;
    }
};

struct PointCloud2 {
    static constexpr const char* IOX2_TYPE_NAME = "PointCloud2";
    
    Header header;
    uint32_t height;
    uint32_t width;
    uint32_t fields_count;
    PointField fields[POINT_FIELD_CAPACITY];
    bool is_bigendian;
    uint32_t point_step;
    uint32_t row_step;
    uint32_t data_length;
    uint8_t data[POINTCLOUD_MAX_DATA_BYTES];
    bool is_dense;
    uint8_t _padding[3];
    
    PointCloud2() {
        memset(this, 0, sizeof(PointCloud2));
        height = 1;
        is_bigendian = false;
        is_dense = false;
    }
    
    const uint8_t* getPointData(size_t index) const {
        if (index >= width || point_step == 0) {
            return nullptr;
        }
        return data + (index * point_step);
    }
    
    uint8_t* getPointData(size_t index) {
        if (index >= width || point_step == 0) {
            return nullptr;
        }
        return data + (index * point_step);
    }
    
    size_t getPointCount() const {
        return width * height;
    }
};

#endif // ICEORYX_POINTCLOUD2_H
