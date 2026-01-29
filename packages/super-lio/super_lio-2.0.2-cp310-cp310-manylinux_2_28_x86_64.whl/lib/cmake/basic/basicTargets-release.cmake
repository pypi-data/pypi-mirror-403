#----------------------------------------------------------------
# Generated CMake target import file for configuration "Release".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "basic::basic" for configuration "Release"
set_property(TARGET basic::basic APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(basic::basic PROPERTIES
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/super_lio/lib/libbasic.so"
  IMPORTED_SONAME_RELEASE "libbasic.so"
  )

list(APPEND _cmake_import_check_targets basic::basic )
list(APPEND _cmake_import_check_files_for_basic::basic "${_IMPORT_PREFIX}/super_lio/lib/libbasic.so" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
