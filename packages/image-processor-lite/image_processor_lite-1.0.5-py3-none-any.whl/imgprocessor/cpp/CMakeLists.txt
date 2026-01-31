cmake_minimum_required(VERSION 3.10)
project(imgprocessor_cpp_modules)

# Configuration
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_FLAGS_RELEASE "-O3 -march=native")
set(CMAKE_CXX_FLAGS_DEBUG "-g -O0")

if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release)
endif()

message(STATUS "Build type: ${CMAKE_BUILD_TYPE}")
message(STATUS "Compiler: ${CMAKE_CXX_COMPILER}")

# ============================================================================
# IMAGE FILTERS LIBRARY
# ============================================================================

add_library(image_filters SHARED
    image_filters.cpp
)

target_compile_options(image_filters PRIVATE
    -fPIC
    -Wall
    -Wextra
)

# ============================================================================
# GEOMETRY UTILS LIBRARY
# ============================================================================

add_library(geometry_utils SHARED
    geometry_utils.cpp
)

target_compile_options(geometry_utils PRIVATE
    -fPIC
    -Wall
    -Wextra
)

# ============================================================================
# INSTALLATION
# ============================================================================

# Les librairies compilées sont placées dans le dossier build
set_target_properties(image_filters PROPERTIES
    LIBRARY_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/lib"
)

set_target_properties(geometry_utils PROPERTIES
    LIBRARY_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/lib"
)

# ============================================================================
# PRINT BUILD INFO
# ============================================================================

message(STATUS "")
message(STATUS "📦 Modules C/C++ compilés:")
message(STATUS "   - image_filters.so")
message(STATUS "   - geometry_utils.so")
message(STATUS "")
message(STATUS "Les librairies seront compilées dans: ${CMAKE_BINARY_DIR}/lib")
message(STATUS "")
